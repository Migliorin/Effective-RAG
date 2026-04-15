import asyncio
from dataclasses import dataclass
from typing import Optional
from queue import Queue
from threading import Thread

from websockets.asyncio.server import ServerConnection, serve

from core import get_dotenv_values
from routes import EXTRACTION_ROUTE, extraction, search_document, SEARCH_ROUTE
from services import AppLogger, ConnectionManager, OCRService, FormatService, QdrantService, LLMService, SearchService

@dataclass
class AppContext:
    logger: object
    queue: Queue
    queue_format: Queue
    connection_manager: ConnectionManager
    ocr_service: OCRService
    format_service: FormatService
    qdrant_service: QdrantService
    llm_service: LLMService
    search_service: SearchService
    worker_thread: Optional[Thread]
    worker_thread_format: Optional[Thread]



@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int


def build_server_config(values: dict) -> ServerConfig:
    host = values.get("HOST", "0.0.0.0")
    port = int(values.get("PORT", 8000))
    return ServerConfig(host=host, port=port)


def build_app_context(values: dict) -> AppContext:
    logger = AppLogger().get_logger()
    queue = Queue()
    queue_format = Queue()
    connection_manager = ConnectionManager()
    ocr_service = OCRService(values, queue, queue_format, logger)
    qdrant_service = QdrantService(values)
    format_service = FormatService(values, queue_format, logger, qdrant_service)
    llm_service=LLMService(values)
    search_service=SearchService(values)

    return AppContext(
        logger=logger,
        queue=queue,
        queue_format=queue_format,
        connection_manager=connection_manager,
        ocr_service=ocr_service,
        format_service=format_service,
        qdrant_service=qdrant_service,
        llm_service=llm_service,
        search_service=search_service,
        worker_thread=None,
        worker_thread_format=None

    )


def start_extraction_worker(app_context: AppContext) -> None:
    if app_context.worker_thread is None or not app_context.worker_thread.is_alive():
        app_context.worker_thread = Thread(
            target=app_context.ocr_service.extract_ocr_pages,
            name="ocr-extraction-worker",
        )
        app_context.worker_thread.start()

    if app_context.worker_thread_format is None or not app_context.worker_thread_format.is_alive():
        app_context.worker_thread_format = Thread(
            target=app_context.format_service.format_text,
            name="format-text-worker",
        )
        app_context.worker_thread_format.start()


def stop_extraction_worker(app_context: AppContext) -> None:
    workers = [
        (app_context.queue, app_context.worker_thread, "worker_thread"),
        (app_context.queue_format, app_context.worker_thread_format, "worker_thread_format"),
    ]

    for queue_, worker_, attr_name in workers:
        if worker_ is not None and worker_.is_alive():
            queue_.put(None)
            worker_.join()
        setattr(app_context, attr_name, None)


async def websocket_router(websocket: ServerConnection, app_context: AppContext):
    path = websocket.request.path
    routes = {
        EXTRACTION_ROUTE: extraction,
        SEARCH_ROUTE: search_document

    }

    handler = routes.get(path)
    if handler is None:
        app_context.logger.warning("Rota websocket nao encontrada: %s", path)
        await websocket.close(code=1008, reason="Rota websocket invalida.")
        return

    await handler(websocket, app_context)


async def main():
    values = get_dotenv_values()
    server_config = build_server_config(values)
    app_context = build_app_context(values)
    logger = app_context.logger
    logger.info("Inicializando recursos da aplicacao")
    start_extraction_worker(app_context)

    try:
        async with serve(
            lambda websocket: websocket_router(websocket, app_context),
            server_config.host,
            server_config.port,
            logger=logger,
        ):
            logger.info(
                "Servidor websocket escutando em ws://%s:%s",
                server_config.host,
                server_config.port,
            )
            await asyncio.Future()
    finally:
        logger.info("Encerrando recursos da aplicacao")
        stop_extraction_worker(app_context)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
