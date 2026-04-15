from prompts import INIT_PROMPT, FINAL_ANSWER
import json


class SearchService:
    def __init__(self,values:dict):
        self.limit_retries_chunks = int(values.get("LIMIT_RETRIES_CHUNKS"))
    
    def query_chunks(self, txt:str,document_id:str,qdrant_service)->list[dict]:
        chunks = qdrant_service.search(txt,document_id)
        chunks = [{"text":chunk.get("text","")[:1200],"score":chunk.get("score","")} for chunk in chunks]
        return chunks

    def query_question(self, txt:str,chunks:list[dict],prompt:str,llm_service,params=None)->dict:
        planner_messages = self.build_planner_messages(txt, chunks, prompt)
        planner_raw = llm_service.call_chat(planner_messages,params=params)
        return planner_raw
    
    def build_planner_messages(self, user_query: str,chunks: list[dict],prompt:str) -> list[dict]:
        return [
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": (
                    f"Contexto: {chunks}"
                    f"Pergunta do usuário:\n{user_query}"
                ),
            },
        ]
    
    def search(self,user_query:str,document_id:str,llm_service, qdrant_service, logger):
        chunks_list = []
        i = 0
        limit = self.limit_retries_chunks
        
        initial_question = user_query[::]
        while(i < limit):
            logger.info("[%s/%s] Processando query: %s",i+1,limit,user_query)
            chunks_list.extend(self.query_chunks(user_query,document_id,qdrant_service))
            response = self.query_question(user_query,chunks_list,INIT_PROMPT,llm_service)
            response = json.loads(response)
            
            type_ = response.get("type","")
            
            if(type_ == "search"):
                user_query = response.get("answer","")
                if(i == limit - 1):
                    break
                i += 1
                continue
            else:
                break
        
        params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "min_p": 0.05,
            "repeat_penalty": 1.1,
            "repeat_last_n": 128,
            "seed": 23847293,
            "num_ctx":8192,
        }
        
        chunks_list = "".join([x["text"] for x in chunks_list])
        chunks_list = chunks_list.strip()
        return self.query_question(
            initial_question,
            chunks_list,
            FINAL_ANSWER,
            llm_service,
            params=params
        )
    