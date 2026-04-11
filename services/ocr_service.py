import json
import os

from processing import PDF
from models import OcrExtraction
from services import BucketMinio

from uuid import uuid4

class OCRService():
    def __init__(self, values: dict, queue, logger):
        self.minio_client = BucketMinio(
            endpoint=values.get("MINIO_ENDPOINT"),
            access_key=values.get("MINIO_ACCESS_KEY"),
            secret_key=values.get("MINIO_SECRET_KEY"),
            secure=False,
        )
        self.pdf_processing =  PDF()
        self.ocr_ext = OcrExtraction()
        self.logger = logger
        self.queue = queue
        self.bucket_name = values.get("BUCKET_EXTRATION")

    def extract_ocr_pages(self):
        logger = self.logger
        minio_client = self.minio_client
        pdf_processing = self.pdf_processing
        ocr_ext = self.ocr_ext

        list_paths = None
        document_path = None
        pages = [-1]

        while(True):
            tarefa = self.queue.get()  # bloqueia até chegar algo
            if tarefa is None:
                logger.info("Encerrando serviço de extração")
                break

            logger.info(f"Tarefa recebida: {json.dumps(tarefa, indent=1)}")

            job_id = tarefa.get("id")
            bucket_name = tarefa.get("bucket_name")
            object_name = tarefa.get("object_name")

            exist_folder = minio_client.verify_folder(self.bucket_name,job_id)

            if(exist_folder):
                logger.info(f"Job id existente no bucket {job_id}")
                pages = minio_client.get_pages(self.bucket_name,job_id)
                logger.info(f"Paginas extraidas: {json.dumps(pages)}")

            try:
                logger.info(
                    "Iniciando download do PDF no MinIO. bucket=%s object_name=%s",
                    bucket_name,
                    object_name,
                )

                document_path: str = minio_client.download_pdf(
                    bucket_name=bucket_name,
                    object_name=object_name,
                )
                logger.info("Download em %s", document_path)

                list_paths: list[str] = pdf_processing.extract_pages_into_imgs(document_path)
                logger.info(f"Imagens extraidas em:\n{json.dumps(list_paths, indent=1)}")
 
                logger.info("Iniciando extração")
                for idx, list_path_ in enumerate(list_paths,start=1):
                    if(idx <= pages[-1]):
                        continue
                    text = ocr_ext(list_path_)
                    path_extract = f"{job_id}/{uuid4()}.json"
                    minio_client.put_json(
                        self.bucket_name,
                        path_extract,
                        {
                            **tarefa,
                            "content": text,
                            "page": idx,
                            "total_pages": len(list_paths)
                        }
                    )
                    logger.info("Texto extraído:\n%s\n", text[:50])
                    logger.info(f"Armazenando extracao em: {path_extract}")
                pages = [-1]
                logger.info("Iniciando finalizada")

            except Exception as exc:
                logger.exception("Erro ao processar job_id=%s\n%s", job_id,exc)

            finally:
                if(list_paths is not None):
                    for list_path_ in list_paths:
                        if os.path.exists(list_path_):
                            os.remove(list_path_)
                elif(document_path is not None):
                    if os.path.exists(document_path):
                        os.remove(document_path)

