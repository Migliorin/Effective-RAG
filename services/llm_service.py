import re

from openai import OpenAI


class LLMService:
    def __init__(self, values: dict):
        self.client_openai = OpenAI(
            base_url=values.get("OPENAI_URL"),
            api_key=values.get("OPENAI_KEY"),
        )
        self.params = {
            "temperature": 0.2,
            "top_p": 0.85,
            "top_k": 30,
            "min_p": 0.0,
            "repeat_penalty": 1.12,
            "repeat_last_n": 128,
            "seed": 42,
        }

    def call_chat(self, messages:list, think=True, model="llama", params=None) -> str:
        if params is None:
            params = self.params
            
        else:
            params_ = self.params.copy()
            params = params_.update(params)

        completion = self.client_openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=params["temperature"],
            top_p=params["top_p"],
            extra_body={
                "num_ctx": params.get("num_ctx", 4096),
                "top_k": params["top_k"],
                "min_p": params["min_p"],
                "repeat_penalty": params["repeat_penalty"],
                "repeat_last_n": params["repeat_last_n"],
                "seed": params["seed"],
            },
        )

        res_final = completion.choices[0].message.content
        res_final = re.sub(r"<think>.*?</think>", "", res_final, flags=re.DOTALL)

        return res_final.strip()
