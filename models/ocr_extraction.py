from transformers import AutoModelForImageTextToText, AutoProcessor


class OcrExtraction:
    def __init__(self, model_path="zai-org/GLM-OCR"):
        self.processor = AutoProcessor.from_pretrained(model_path)
        self.model = AutoModelForImageTextToText.from_pretrained(
            pretrained_model_name_or_path=model_path,
            torch_dtype="auto",
            device_map="auto",
        )

    def __call__(self, path: str):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "url": path},
                    {"type": "text", "text": "Table Recognition:"},
                ],
            }
        ]
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)
        inputs.pop("token_type_ids", None)
        generated_ids = self.model.generate(**inputs, max_new_tokens=8192)
        output_text = self.processor.decode(
            generated_ids[0][inputs["input_ids"].shape[1] :], skip_special_tokens=False
        )
        return output_text
