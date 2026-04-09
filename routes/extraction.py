from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter(prefix="/extraction")


def parse_extraction_protocol(data: str) -> tuple[str, str]:
    bucket, separator, path_document = data.partition(":")

    if not separator or not bucket or not path_document:
        raise ValueError("Payload invalido. Use o formato 'bucket:path_document'.")

    return bucket, path_document


@router.websocket("/ocr")
async def extraction(websocket: WebSocket):
    manager = websocket.app.state.connection_manager
    logger = websocket.app.state.logger
    minio_client = websocket.app.state.minio_client
    pdf_processing = websocket.app.state.pdf_processing

    await manager.connect(websocket)
    logger.info("WebSocket conectado em /extraction/ocr")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info("Mensagem recebida no websocket de OCR: %s", data)
            try:
                bucket_name, object_name = parse_extraction_protocol(data)
            except ValueError as exc:
                logger.warning("Payload invalido recebido no websocket de OCR: %s", data)
                await manager.send_personal_message(str(exc), websocket)
                continue

            await manager.send_personal_message(
                f"Received bucket={bucket_name} path_document={object_name}",
                websocket,
            )
            logger.info(
                "Iniciando download do PDF no MinIO. bucket=%s object_name=%s",
                bucket_name,
                object_name,
            )
            document_path:str = minio_client.download_pdf(
                bucket_name=bucket_name,
                object_name=object_name,
            )
            logger.info("Download em %s",document_path)

            list_paths: list[str] = pdf_processing.extract_pages_into_imgs(document_path)

            logger.info(f"Imagens extraidas em:\n{json.dumps(list_paths,indent=1)}",)

    except WebSocketDisconnect:
        logger.info("WebSocket desconectado em /extraction/ocr")
        manager.disconnect(websocket)
    except Exception:
        logger.exception("Erro durante o processamento do websocket de OCR")
        manager.disconnect(websocket)
