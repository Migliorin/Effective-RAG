from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling.document_converter import DocumentConverter
from transformers import AutoTokenizer
from .llm_openai import LlmOpenAi

from docling.chunking import HybridChunker

class Chunknizer():
    def __init__(self,tokenizer_id:str,max_tokens:int,embedder:LlmOpenAi):
        self.tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(tokenizer_id),
            max_tokens=max_tokens
        )

        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            merge_peers=True,
        )

        self.embedder = embedder


    def create_chunker_from_md(self,path_md:str)->list[str]:
        doc = DocumentConverter().convert(source=path_md).document
        chunk_iter = self.chunker.chunk(dl_doc=doc)
        chunks = list(chunk_iter)
        return [x.text for x in chunks]

    def embedding_chunks(self,chunks:list[str],model="qwen3-06b-emb")->list[list[float]]:
        embeddings = self.embedder.embedding_call(
            model=model,
            list_text=chunks
        )

        return embeddings
