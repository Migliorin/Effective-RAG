# Effective RAG

Effective RAG is a Python backend for document ingestion, OCR, chunking, vector indexing, and document-scoped question answering over WebSockets.

The application receives PDF references from MinIO, extracts each page as an image, runs OCR with `zai-org/GLM-OCR`, stores page-level extraction artifacts back in MinIO, formats the extracted text with an OpenAI-compatible chat API, chunks the generated Markdown with Docling, indexes the chunks in Qdrant, and answers user questions by retrieving and reranking document chunks.

# License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
