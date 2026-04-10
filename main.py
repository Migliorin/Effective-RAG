import asyncio
from dataclasses import dataclass
from typing import Optional
from queue import Queue
from threading import Thread

from websockets.asyncio.server import ServerConnection, serve

from core import get_dotenv_values
from routes import EXTRACTION_ROUTE, extraction
from services import AppLogger, ConnectionManager, OCRService

@dataclass
class AppContext:
    logger: object
    queue: Queue
    connection_manager: ConnectionManager
    ocr_service: OCRService
    worker_thread: Optional[Thread]


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
    connection_manager = ConnectionManager()
    ocr_service = OCRService(values, queue, logger)

    return AppContext(
        logger=logger,
        queue=queue,
        connection_manager=connection_manager,
        ocr_service=ocr_service,
        worker_thread=None,
    )


def start_extraction_worker(app_context: AppContext) -> Thread:
    if app_context.worker_thread is not None and app_context.worker_thread.is_alive():
        return app_context.worker_thread

    worker_thread = Thread(target=app_context.ocr_service.extract_ocr_pages, name="ocr-extraction-worker")
    worker_thread.start()
    app_context.worker_thread = worker_thread
    return worker_thread


def stop_extraction_worker(app_context: AppContext):
    worker_thread = app_context.worker_thread
    if worker_thread is None:
        return

    if worker_thread.is_alive():
        app_context.queue.put(None)
        worker_thread.join()

    app_context.worker_thread = None


async def websocket_router(websocket: ServerConnection, app_context: AppContext):
    path = websocket.request.path
    routes = {
        EXTRACTION_ROUTE: extraction,
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
