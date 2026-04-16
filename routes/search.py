import json
import uuid

from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

SEARCH_ROUTE = "/search/document"


def parse_extraction_protocol(data: str) -> tuple[str, str]:
    bucket, separator, path_document = data.partition(":")

    if not separator or not bucket or not path_document:
        raise ValueError("Payload invalido. Use o formato 'bucket:path_document'.")

    return bucket, path_document


async def search_document(websocket: ServerConnection, app_context):
    manager = app_context.connection_manager
    logger = app_context.logger
    qdrant_service = app_context.qdrant_service
    llm_service = app_context.llm_service
    search_service = app_context.search_service
    connection_id = str(uuid.uuid4())

    await manager.connect(connection_id, websocket)
    logger.info(
        "WebSocket conectado em %s connection_id=%s", SEARCH_ROUTE, connection_id
    )

    try:
        async for data in websocket:
            logger.info("Mensagem recebida no websocket de busca: %s", data)

            try:
                document_id, user_query = parse_extraction_protocol(data)
            except ValueError as exc:
                logger.warning(
                    "Payload invalido recebido no websocket de busca: %s", data
                )
                await manager.send_personal_message(str(exc), websocket)
                continue

            initial_question = user_query[::]

            response: str = search_service.search(
                user_query, document_id, llm_service, qdrant_service, logger
            )

            logger.info("Resposta da IA: \n%s", response)

            await manager.send_personal_message(
                json.dumps(
                    {
                        "document_id": document_id,
                        "query": initial_question,
                        "answer": response,
                    },
                    ensure_ascii=False,
                ),
                websocket,
            )

    except ConnectionClosed:
        logger.info(
            "WebSocket desconectado em %s connection_id=%s", SEARCH_ROUTE, connection_id
        )
        manager.disconnect(connection_id)
    except Exception:
        logger.exception("Erro durante o processamento do websocket de busca")
        manager.disconnect(connection_id)
    else:
        logger.info(
            "WebSocket encerrado pelo cliente em %s connection_id=%s",
            SEARCH_ROUTE,
            connection_id,
        )
        manager.disconnect(connection_id)
