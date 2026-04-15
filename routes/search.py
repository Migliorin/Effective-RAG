import json
import uuid

from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

SEARCH_ROUTE = "/search/document"
MAX_RAG_STEPS = 20
MIN_UNIQUE_CHUNKS_FOR_EVIDENCE = 3


def parse_search_protocol(data: str) -> tuple[str, str]:
    document_id, separator, query = data.partition(":")

    if not separator or not document_id or not query:
        raise ValueError("Payload invalido. Use o formato 'document_id:query'.")

    return document_id, query


def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        return None

def build_planner_messages(user_query: str, rag_history: list[dict]) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Você é um planejador iterativo para busca em RAG.\n"
                "Seu trabalho é analisar a pergunta do usuário e quebrá-la em perguntas atômicas, "
                "ou seja, uma pergunta por vez.\n"
                "Se a entrada do usuário contiver mais de uma pergunta, pedido ou intenção, você deve escolher "
                "apenas UMA para tratar na rodada atual: a mais prioritária ou a próxima ainda não respondida.\n"
                "Você deve decidir, a cada rodada, qual pergunta atômica será tratada agora e qual subconsulta "
                "deve ser executada para buscar no RAG.\n"
                "Você decide quando continuar buscando e quando já existe contexto suficiente para responder "
                "à pergunta atômica atual.\n\n"
                "Retorne EXCLUSIVAMENTE um JSON válido, sem markdown, sem texto extra, no formato:\n"
                "{\n"
                '  "action": "search" ou "final",\n'
                '  "current_question": "pergunta atomica atual",\n'
                '  "query": "subconsulta para buscar no RAG agora",\n'
                '  "what_is_doing": "explicação curta do passo atual",\n'
                '  "sub_steps": ["etapa 1", "etapa 2", "etapa 3"],\n'
                '  "remaining_questions": ["pergunta atomica 2", "pergunta atomica 3"],\n'
                '  "missing_information": "o que ainda falta descobrir para responder bem a pergunta atomica atual"\n'
                "}\n\n"
                "Regras:\n"
                "- Sempre destrinche a entrada do usuário em perguntas atômicas.\n"
                "- Trabalhe somente UMA pergunta atômica por rodada.\n"
                "- Nunca misture duas perguntas diferentes na mesma query.\n"
                "- O campo current_question deve conter apenas a pergunta atual.\n"
                "- O campo remaining_questions deve conter as demais perguntas ainda não tratadas.\n"
                "- Gere apenas uma subconsulta por rodada, focada na pergunta atômica atual.\n"
                "- Use action='search' se ainda faltar contexto.\n"
                "- Use action='final' somente quando o contexto acumulado já for suficiente para responder a pergunta atômica atual.\n"
                "- Preserve a intenção original do usuário.\n"
                "- A query deve ser boa para busca semântica e lexical.\n"
                "- O campo what_is_doing deve ser curto e objetivo.\n"
                "- O campo sub_steps deve conter as pequenas etapas da análise da pergunta atual.\n"
                "- Nunca retorne nada fora do JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Pergunta original do usuário:\n{user_query}\n\n"
                f"Histórico do processo RAG até agora:\n{json.dumps(rag_history, ensure_ascii=False, indent=2)}"
            ),
        },
    ]

# def build_planner_messages(user_query: str, rag_history: list[dict]) -> list[dict]:
#     return [
#         {
#             "role": "system",
#             "content": (
#                 "Você é um planejador iterativo para busca em RAG.\n"
#                 "Seu trabalho é destrinchar a pergunta do usuário em pequenas etapas e decidir, a cada rodada, "
#                 "qual subconsulta deve ser executada agora.\n"
#                 "Você decide quando continuar buscando e quando já existe contexto suficiente para responder.\n"
#                 "Retorne EXCLUSIVAMENTE um JSON válido, sem markdown, sem texto extra, no formato:\n"
#                 "{\n"
#                 '  "action": "search" ou "final",\n'
#                 '  "query": "subconsulta para buscar no RAG agora",\n'
#                 '  "what_is_doing": "explicação curta do passo atual",\n'
#                 '  "sub_steps": ["etapa 1", "etapa 2", "etapa 3"],\n'
#                 '  "missing_information": "o que ainda falta descobrir para responder bem"\n'
#                 "}\n"
#                 "Regras:\n"
#                 "- Divida a pergunta em pequenas etapas lógicas.\n"
#                 "- Gere apenas uma subconsulta por rodada, focada na próxima pequena etapa.\n"
#                 "- Use action='search' se ainda faltar contexto.\n"
#                 "- Use action='final' somente quando o contexto acumulado já for suficiente.\n"
#                 "- Preserve a intenção original do usuário.\n"
#                 "- A query deve ser boa para busca semântica e lexical.\n"
#                 "- O campo what_is_doing deve ser curto e objetivo.\n"
#                 "- O campo sub_steps deve conter as pequenas etapas da análise.\n"
#                 "- Nunca retorne nada fora do JSON."
#             ),
#         },
#         {
#             "role": "user",
#             "content": (
#                 f"Pergunta original do usuário:\n{user_query}\n\n"
#                 f"Histórico do processo RAG até agora:\n{json.dumps(rag_history, ensure_ascii=False, indent=2)}"
#             ),
#         },
#     ]


def parse_planner_response(raw_response: str, original_query: str) -> dict:
    data = safe_json_loads(raw_response)

    if not isinstance(data, dict):
        return {
            "action": "search",
            "query": original_query,
            "what_is_doing": "Falha ao planejar. Usando a pergunta original para buscar contexto.",
            "sub_steps": ["Entender a pergunta original", "Buscar contexto principal", "Tentar responder"],
            "missing_information": "Contexto relevante do documento.",
        }

    action = str(data.get("action", "search")).strip().lower()
    if action not in {"search", "final"}:
        action = "search"

    query = str(data.get("query", "")).strip() or original_query
    what_is_doing = str(data.get("what_is_doing", "")).strip() or "Executando uma etapa de busca no RAG."
    missing_information = str(data.get("missing_information", "")).strip() or "Validando se já há contexto suficiente."

    sub_steps = data.get("sub_steps", [])
    if not isinstance(sub_steps, list):
        sub_steps = []

    sub_steps = [str(item).strip() for item in sub_steps if str(item).strip()]
    if not sub_steps:
        sub_steps = ["Interpretar a pergunta", "Buscar contexto relevante", "Consolidar resposta"]

    return {
        "action": action,
        "query": query,
        "what_is_doing": what_is_doing,
        "sub_steps": sub_steps,
        "missing_information": missing_information,
    }


def deduplicate_chunks(chunks: list[dict], seen_chunk_ids: set) -> list[dict]:
    unique_chunks = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        dedup_key = str(chunk_id) if chunk_id is not None else json.dumps(chunk, ensure_ascii=False, sort_keys=True)

        if dedup_key in seen_chunk_ids:
            continue

        seen_chunk_ids.add(dedup_key)
        unique_chunks.append(chunk)

    return unique_chunks


def format_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        [
            f"[chunk_id={chunk.get('chunk_id', 'unknown')}]\n{chunk.get('contextualized_text', '')}"
            for chunk in chunks
        ]
    )


def build_evidence_messages(user_query: str, rag_history: list[dict], all_chunks: list[dict]) -> list[dict]:
    compact_chunks = [
        {
            "chunk_id": chunk.get("chunk_id"),
            "text": chunk.get("contextualized_text", "")[:1200],
        }
        for chunk in all_chunks[:12]
    ]

    return [
        {
            "role": "system",
            "content": (
                "Você é um avaliador de suficiência de evidências para RAG.\n"
                "Decida se o contexto acumulado já é suficiente para responder a pergunta do usuário com segurança.\n"
                "Retorne EXCLUSIVAMENTE um JSON válido no formato:\n"
                "{\n"
                '  "sufficient_evidence": true ou false,\n'
                '  "reason": "explicação curta e objetiva"\n'
                "}\n"
                "Regras:\n"
                "- Responda true apenas se o contexto recuperado já for suficiente.\n"
                "- Responda false se ainda faltar informação essencial.\n"
                "- Nunca retorne nada fora do JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Pergunta do usuário:\n{user_query}\n\n"
                f"Histórico do RAG:\n{json.dumps(rag_history, ensure_ascii=False, indent=2)}\n\n"
                f"Contexto acumulado:\n{json.dumps(compact_chunks, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def parse_evidence_response(raw_response: str) -> dict:
    data = safe_json_loads(raw_response)

    if not isinstance(data, dict):
        return {
            "sufficient_evidence": False,
            "reason": "Falha ao avaliar suficiência de evidências.",
        }

    return {
        "sufficient_evidence": bool(data.get("sufficient_evidence", False)),
        "reason": str(data.get("reason", "")).strip() or "Avaliação de evidências concluída.",
    }


def has_sufficient_evidence(
    llm_service,
    user_query: str,
    rag_history: list[dict],
    all_chunks: list[dict],
) -> dict:
    if len(all_chunks) < MIN_UNIQUE_CHUNKS_FOR_EVIDENCE:
        return {
            "sufficient_evidence": False,
            "reason": f"Ainda ha poucos chunks unicos acumulados ({len(all_chunks)}).",
        }

    messages = build_evidence_messages(user_query, rag_history, all_chunks)
    raw = llm_service.call_chat(messages, think=False).strip()
    return parse_evidence_response(raw)


def build_final_answer_messages(user_query: str, all_chunks: list[dict], rag_history: list[dict]) -> list[dict]:
    context = format_context(all_chunks)

    return [
        {
            "role": "system",
            "content": (
                "Você responde perguntas usando apenas o contexto recuperado do documento e todo o histórico do processo RAG.\n"
                "Use o histórico para entender as pequenas etapas executadas, as subconsultas feitas e o que foi buscado em cada passo.\n"
                "Se a resposta não estiver no contexto recuperado, diga isso claramente.\n"
                "Seja objetivo."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Pergunta original do usuário:\n{user_query}\n\n"
                f"Histórico completo do processo RAG:\n{json.dumps(rag_history, ensure_ascii=False, indent=2)}\n\n"
                f"Contexto recuperado do documento:\n{context}\n\n"
                "Responda com base apenas no contexto recuperado."
            ),
        },
    ]


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
                document_id, user_query = parse_search_protocol(data)
            except ValueError as exc:
                logger.warning("Payload invalido recebido no websocket de busca: %s", data)
                await manager.send_personal_message(str(exc), websocket)
                continue

            rag_history = []
            all_chunks = []
            seen_chunk_ids = set()

            step_number = 1
            while step_number <= MAX_RAG_STEPS:
                planner_messages = build_planner_messages(user_query, rag_history)
                planner_raw = llm_service.call_chat(planner_messages, think=False).strip()
                planner = parse_planner_response(planner_raw, user_query)

                action = planner["action"]
                rag_query = planner["query"]
                what_is_doing = planner["what_is_doing"]
                sub_steps = planner["sub_steps"]
                missing_information = planner["missing_information"]

                step_trace = {
                    "step": step_number,
                    "action": action,
                    "query": rag_query,
                    "what_is_doing": what_is_doing,
                    "sub_steps": sub_steps,
                    "missing_information": missing_information,
                }

                logger.info(
                    "RAG step=%s action=%s query=%s what_is_doing=%s",
                    step_number,
                    action,
                    rag_query,
                    what_is_doing,
                )

                if action == "final":
                    step_trace["status"] = "planner_finalized"
                    rag_history.append(step_trace)
                    break

                chunks = qdrant_service.search(
                    query=rag_query,
                    document_id=document_id,
                    limit=100,
                    rerank_limt=5,
                )

                unique_chunks = deduplicate_chunks(chunks, seen_chunk_ids)
                all_chunks.extend(unique_chunks)

                step_trace["retrieved_chunks"] = len(chunks)
                step_trace["new_chunks"] = len(unique_chunks)
                step_trace["retrieved_chunk_ids"] = [chunk.get("chunk_id") for chunk in unique_chunks]

                evidence_eval = has_sufficient_evidence(
                    llm_service=llm_service,
                    user_query=user_query,
                    rag_history=rag_history + [step_trace],
                    all_chunks=all_chunks,
                )

                step_trace["sufficient_evidence"] = evidence_eval["sufficient_evidence"]
                step_trace["evidence_reason"] = evidence_eval["reason"]
                step_trace["status"] = (
                    "search_executed_with_sufficient_evidence"
                    if evidence_eval["sufficient_evidence"]
                    else "search_executed"
                )

                rag_history.append(step_trace)

                if evidence_eval["sufficient_evidence"]:
                    logger.info(
                        "Parando por evidencia suficiente no step=%s reason=%s",
                        step_number,
                        evidence_eval["reason"],
                    )
                    break

                step_number += 1

            if not all_chunks and (not rag_history or rag_history[-1]["action"] != "final"):
                await manager.send_personal_message(
                    json.dumps(
                        {
                            "document_id": document_id,
                            "query": user_query,
                            "cot": rag_history,
                            "answer": "Nenhum trecho relevante encontrado para este documento.",
                            "chunks": [],
                        },
                        ensure_ascii=False,
                    ),
                    websocket,
                )
                continue

            final_messages = build_final_answer_messages(user_query, all_chunks, rag_history)
            answer = llm_service.call_chat(final_messages, think=True)

            response = {
                "document_id": document_id,
                "query": user_query,
                "cot": rag_history,
                "answer": answer,
                "chunks": all_chunks,
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