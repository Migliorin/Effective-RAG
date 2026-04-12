from services import AppLogger
from services import BucketMinio

from queue import Queue
from openai import OpenAI

import re


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
- Corrija apenas quebras de linha erradas
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
    def __init__(self, values: dict, queue_format: Queue, logger:AppLogger):
        self.minio_client = BucketMinio(
            endpoint=values.get("MINIO_ENDPOINT"),
            access_key=values.get("MINIO_ACCESS_KEY"),
            secret_key=values.get("MINIO_SECRET_KEY"),
            secure=False,
        )
        self.client_openai = OpenAI(
            base_url=values.get("OPENAI_URL"),
            api_key=values.get("OPENAI_KEY")
        )
        self.logger = logger
        self.queue_format = queue_format
        self.bucket_name = values.get("BUCKET_EXTRATION")

    def call_chat(self, messages, think=True) -> str:
        params = {
            "temperature": 0.6 if think else 0.7,
            "top_p": 0.95 if think else 0.8
        }

        completion = self.client_openai.chat.completions.create(
            model="qwen3",
            messages=messages,
            **params
        )

        res_final = completion.choices[0].message.content
        res_final = re.sub(r"<think>.*?<\/think>", "", res_final, flags=re.DOTALL)

        return res_final



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
                for path_extract in list_extraction:
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
                        res = self.call_chat(messages,think=False)
                        md_list.append(res)
                logger.info("União finalizada")