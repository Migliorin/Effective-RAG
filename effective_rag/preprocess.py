import re
import pandas as pd
from io import StringIO


def clean_sections(text:str)->str:
    m = re.search(r"^(?:[a-zA-Z]\)|\d+\.\d+|\d+\.)", text)
    if(m):
        _, end = m.span()
        return text[end+1 :]
    else:
        return text


class Preprocess():
    def __init__(self):
        pass

    def __call__(self, class_id: int, text: str) -> str:
        if class_id == 4:
            return "<Figure>"

        if class_id == 5:
           return f"\n*Figure: {text}*\n"

        if class_id == 10:
            return f"\n{text}\n"

        if class_id == 12:
            return f"\n# {clean_sections(text)}\n"

        if class_id == 13:
            return f"\n## {clean_sections(text)}\n"

        if class_id == 14:
            return f"\n### {clean_sections(text)}\n"

        if class_id == 15:
            if("<table" in text):
                tables = pd.read_html(StringIO(text))

                return "\n" + "\n\n".join(table.to_markdown() for table in tables) + "\n"
            else:
                return f"\n{text}\n"

        if class_id == 16:
            return f"\n*Table: {text}*\n"

        return ""
