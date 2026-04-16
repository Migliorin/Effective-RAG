import json
from queue import Queue

from dto import FormatExtractionDto
from prompts import FORMAT_PROMPT
from services import AppLogger, BucketMinio

from .docling_service import DoclingService
from .llm_service import LLMService
from .qdrant_service import QdrantService


class FormatService:
    def __init__(
        self,
        values: dict,
        queue_format: Queue,
        logger: AppLogger,
        qdrant_service: QdrantService,
    ):
        self.minio_client = BucketMinio(
            endpoint=values.get("MINIO_ENDPOINT"),
            access_key=values.get("MINIO_ACCESS_KEY"),
            secret_key=values.get("MINIO_SECRET_KEY"),
            secure=False,
        )
        self.docling = DoclingService()
        self.client_openai = LLMService(values)
        self.bucket_name = values.get("BUCKET_EXTRATION")
        self.debug_format = values.get("DEBUG_FORMAT", False)
        self.range_union_format_page = int(values.get("RANGE_UNION_FORMAT_PAGE", 2))
        self.logger = logger
        self.queue_format = queue_format
        self.qdrant_service = qdrant_service

    def format_text(self):
        logger = self.logger
        minio_client = self.minio_client
        while True:
            tarefa: FormatExtractionDto = (
                self.queue_format.get()
            )  # bloqueia até chegar algo
            if tarefa is None:
                logger.info("Encerrando serviço de formatação")
                break

            list_extraction: list[str] = tarefa.list_extraction
            job_id: str = tarefa.job_id

            if list_extraction:
                md_list = list()
                buffer_contents = []

                logger.info(
                    f"Iniciando união ({len(list_extraction)} jsons) dos conteúdos do job: {job_id}"
                )

                for idx, path_extract in enumerate(list_extraction, start=1):
                    logger.info(f"União [{idx}/{len(list_extraction)}]")

                    obj: dict = minio_client.get_json_object(
                        self.bucket_name, path_extract
                    )
                    content_string = obj.get("content", "")

                    if len(content_string) != 0:
                        buffer_contents.append(content_string)

                    if len(buffer_contents) == 2 or idx == len(list_extraction):
                        if buffer_contents:
                            joined_content = "\n\n".join(buffer_contents)

                            messages = [
                                {"role": "system", "content": FORMAT_PROMPT},
                                {
                                    "role": "user",
                                    "content": f"Converta o texto abaixo para Markdown:\n\n{joined_content}",
                                },
                            ]

                            res = self.client_openai.call_chat(
                                messages,
                                think=False,
                            )
                            md_list.append(res)
                            buffer_contents = []

                logger.info("União finalizada")

                md_list_join:str = "".join(md_list)
                
                chunks = self.docling.create_chunks(md_list_join)

                if self.debug_format:
                    with open("./tmp.json", "w+") as outfile:
                        json.dump(chunks, outfile, ensure_ascii=False, indent=2)
                        outfile.close()

                    with open("./tmp.md", "w+") as outfile:
                        outfile.write(md_list_join)
                        outfile.close()

                logger.info(
                    f"Inserção de {len(chunks)} chunks na collection {self.qdrant_service.collection_name}"
                )
                self.qdrant_service.add_chunks(document_id=job_id, chunks=chunks)
