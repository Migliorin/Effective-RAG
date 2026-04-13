from docling.document_converter import DocumentConverter, InputFormat
from docling.chunking import HybridChunker


class DoclingService():
    def __init__(self):
        self.converter = DocumentConverter()
        self.chunker = HybridChunker()

    def create_chunks(self,markdown_text:str)->list[dict]:
        
        doc = self.converter.convert_string(
            content=markdown_text,
            format=InputFormat.MD,
            name="mem.md",
        ).document

        result = []
        for i, chunk in enumerate(self.chunker.chunk(dl_doc=doc), 1):
            result.append({
                "id": i,
                "text": chunk.text,
                "contextualized_text": self.chunker.contextualize(chunk),
                "meta": chunk.meta.model_dump() if hasattr(chunk.meta, "model_dump") else str(chunk.meta),
            })

        return result