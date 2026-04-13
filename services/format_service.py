from services import AppLogger
from services import BucketMinio
from .docling_service import DoclingService
from .qdrant_service import QdrantService
from .llm_service import LLMService

from queue import Queue

import re
import json


system_prompt = """
Você converte texto extraído de PDF para Markdown.

REGRAS CRÍTICAS:
- Retorne SOMENTE Markdown
- NÃO explique nada
- NÃO use blocos de código
- NÃO adicione conteúdo
- NÃO interprete o texto
- NÃO reescreva frases

PROCESSAMENTO:
- Corrija apenas quebras de linha erradas e palavras
- Una frases quebradas
- Remova apenas:
  - cabeçalhos repetidos
  - rodapés repetidos
  - números de página isolados

FORMATAÇÃO:
- Use títulos (#) apenas se for claramente um título
- Use listas apenas se o texto já parecer lista
- Tabelas quebradas convertas para que eu consiga uní-las com seu complemento da próxima página

Se houver dúvida, mantenha o texto original.
"""

class FormatService():
    def __init__(self, values: dict, queue_format: Queue, logger:AppLogger, qdrant_service: QdrantService):
        self.minio_client = BucketMinio(
            endpoint=values.get("MINIO_ENDPOINT"),
            access_key=values.get("MINIO_ACCESS_KEY"),
            secret_key=values.get("MINIO_SECRET_KEY"),
            secure=False,
        )
        self.docling = DoclingService()
        self.client_openai = LLMService(values)
        self.logger = logger
        self.queue_format = queue_format
        self.bucket_name = values.get("BUCKET_EXTRATION")
        self.qdrant_service = qdrant_service


    def format_text(self):
        logger = self.logger
        minio_client = self.minio_client
        while(True):
            tarefa = self.queue_format.get()  # bloqueia até chegar algo
            if tarefa is None:
                logger.info("Encerrando serviço de formatação")
                break
            
            list_extraction:list = tarefa.get("list_extraction",[])
            job_id:str = tarefa.get("id","")
            
            if(list_extraction):
                md_list = list()
                logger.info(f"Iniciando união ({len(list_extraction)} jsons) dos conteúdos do job: {job_id}")
                for idx, path_extract in enumerate(list_extraction,start=1):
                    logger.info(f"União [{idx}/{len(list_extraction)}]")
                    obj:dict = minio_client.get_json_object(self.bucket_name,path_extract)
                    content_string = obj.get("content","")
                    if(len(content_string) != 0):
                        messages=[
                            {
                                "role": "system", 
                                "content": system_prompt
                            },
                            {
                                "role": "user", 
                                "content": f"Converta o texto abaixo para Markdown:\n\n{content_string}"
                            }
                        ]
                        res = self.client_openai.call_chat(messages,think=False)
                        md_list.append(res)
                logger.info("União finalizada")

            # with open("./tmp.md","r",encoding="utf-8") as outfile:
            #     md_list:str = "".join(outfile.readlines())
            #     outfile.close()

                chunks = self.docling.create_chunks("\n".join(md_list))
                with open("./tmp.json","w+") as outfile:
                    json.dump(chunks,outfile,ensure_ascii=False,indent=2)
                    outfile.close()
                
                logger.info(f"Inserção de {len(chunks)} chunks na collection {self.qdrant_service.collection_name}")
                self.qdrant_service.add_chunks(document_id=job_id, chunks=chunks)
