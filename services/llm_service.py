from openai import OpenAI
import re

class LLMService:
    def __init__(self, values: dict):
        self.client_openai = OpenAI(
            base_url=values.get("OPENAI_URL"),
            api_key=values.get("OPENAI_KEY"),
        )

    def call_chat(self, messages, think=True) -> str:
        params = {
            "temperature": 0.6 if think else 0.7,
            "top_p": 0.95 if think else 0.8,
        }

        completion = self.client_openai.chat.completions.create(
            model="qwen3",
            messages=messages,
            **params,
        )

        res_final = completion.choices[0].message.content
        res_final = re.sub(r"<think>.*?</think>", "", res_final, flags=re.DOTALL)

        return res_final.strip()