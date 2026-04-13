import json
import uuid


from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

SEARCH_ROUTE = "/search/document"


def parse_search_protocol(data: str) -> tuple[str, str]:
    document_id, separator, query = data.partition(":")

    if not separator or not document_id or not query:
        raise ValueError("Payload invalido. Use o formato 'document_id:query'.")

    return document_id, query


async def search_document(websocket: ServerConnection, app_context):
    manager = app_context.connection_manager
    logger = app_context.logger
    qdrant_service = app_context.qdrant_service
    llm_service = app_context.llm_service
    connection_id = str(uuid.uuid4())

    await manager.connect(connection_id, websocket)
    logger.info("WebSocket conectado em %s connection_id=%s", SEARCH_ROUTE, connection_id)

    try:
        async for data in websocket:
            logger.info("Mensagem recebida no websocket de busca: %s", data)

            try:
                document_id, query = parse_search_protocol(data)
            except ValueError as exc:
                logger.warning("Payload invalido recebido no websocket de busca: %s", data)
                await manager.send_personal_message(str(exc), websocket)
                continue

            chunks = qdrant_service.search(query=query, document_id=document_id, limit=15)

            if not chunks:
                await manager.send_personal_message(
                    json.dumps(
                        {
                            "document_id": document_id,
                            "query": query,
                            "answer": "Nenhum trecho relevante encontrado para este documento.",
                            "chunks": [],
                        },
                        ensure_ascii=False,
                    ),
                    websocket,
                )
                continue

            context = "\n\n".join(
                [
                    f"[chunk_id={chunk['chunk_id']}]\n{chunk['contextualized_text']}"
                    for chunk in chunks
                ]
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Você responde perguntas usando apenas o contexto recuperado do documento. "
                        "Se a resposta não estiver no contexto, diga isso claramente. "
                        "Seja objetivo."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Pergunta:\n{query}\n\n"
                        f"Contexto do documento:\n{context}\n\n"
                        "Responda com base apenas no contexto."
                    ),
                },
            ]

            answer = llm_service.call_chat(messages, think=True)

            response = {
                "document_id": document_id,
                "query": query,
                "answer": answer,
                "chunks": chunks,
            }

            await manager.send_personal_message(
                json.dumps(response, ensure_ascii=False),
                websocket,
            )

    except ConnectionClosed:
        logger.info("WebSocket desconectado em %s connection_id=%s", SEARCH_ROUTE, connection_id)
        manager.disconnect(connection_id)
    except Exception:
        logger.exception("Erro durante o processamento do websocket de busca")
        manager.disconnect(connection_id)
    else:
        logger.info("WebSocket encerrado pelo cliente em %s connection_id=%s", SEARCH_ROUTE, connection_id)
        manager.disconnect(connection_id)