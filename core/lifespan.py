from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import get_dotenv_values
from services import AppLogger, BucketMinio
from processing import PDF
from models import OcrExtraction
from services import ConnectionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    values = get_dotenv_values()
    app.state.logger = AppLogger().get_logger()
    app.state.logger.info("Inicializando recursos da aplicacao")

    #app.state.ocr_ext = OcrExtraction()
    app.state.ocr_ext = None
    app.state.minio_client = BucketMinio(
        endpoint=values.get("MINIO_ENDPOINT"),
        access_key=values.get("MINIO_ACCESS_KEY"),
        secret_key=values.get("MINIO_SECRET_KEY"),
        secure=False,
    )
    app.state.pdf_processing = PDF()

    app.state.connection_manager = ConnectionManager()

    yield

    app.state.logger.info("Encerrando recursos da aplicacao")
    app.state.ocr_ext = None
    app.state.minio_client = None
    app.state.pdf_processing = None
    app.state.connection_manager = None
    app.state.logger = None
