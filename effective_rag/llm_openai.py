from openai import OpenAI
import logging

logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

class LlmOpenAi():
    def __init__(self,base_url:str,api_key="no-needed"):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )


    def embedding_call(self, model:str, list_text: list[str])->list[list[float]]:
        embeddings = self.client.embeddings.create(
            model=model,
            input=list_text,
        )
        return [x.embedding for x in embeddings.data]

    def glm_ocr_call(self,img_b64:str,model_name="glm-ocr") -> str:

        response = None

        response = self.client.chat.completions.create(
            model="glm-ocr",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Text Recognition:"},
                        {"type": "image_url", "image_url": {"url": img_b64}},
                    ],
                }
            ],
            temperature=0,
        )

        if(response):
            return response.choices[0].message.content
        else:
            return ""

