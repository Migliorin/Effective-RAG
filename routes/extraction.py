import uuid
import json

from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

EXTRACTION_ROUTE = "/extraction/ocr"


def parse_extraction_protocol(data: str) -> tuple[str, str]:
    bucket, separator, path_document = data.partition(":")

    if not separator or not bucket or not path_document:
        raise ValueError("Payload invalido. Use o formato 'bucket:path_document'.")

    return bucket, path_document


async def extraction(websocket: ServerConnection, app_context):
    manager = app_context.connection_manager
    logger = app_context.logger
    queue = app_context.queue
    connection_id = str(uuid.uuid4())

    await manager.connect(connection_id, websocket)
    logger.info("WebSocket conectado em %s connection_id=%s", EXTRACTION_ROUTE, connection_id)

    try:
        async for data in websocket:
            logger.info("Mensagem recebida no websocket de OCR: %s", data)
            try:
                bucket_name, object_name = parse_extraction_protocol(data)
            except ValueError as exc:
                logger.warning("Payload invalido recebido no websocket de OCR: %s", data)
                await manager.send_personal_message(str(exc), websocket)
                continue

            job_obj = {
                "id": object_name.split("/")[-1].replace(".pdf",""),
                "bucket_name": bucket_name,
                "object_name": object_name,
            }
            queue.put(job_obj)

            await manager.send_personal_message(f"Job iniciado: {json.dumps(job_obj)}", websocket)

    except ConnectionClosed:
        logger.info("WebSocket desconectado em %s connection_id=%s", EXTRACTION_ROUTE, connection_id)
        manager.disconnect(connection_id)
    except Exception:
        logger.exception("Erro durante o processamento do websocket de OCR")
        manager.disconnect(connection_id)
    else:
        logger.info("WebSocket encerrado pelo cliente em %s connection_id=%s", EXTRACTION_ROUTE, connection_id)
        manager.disconnect(connection_id)
