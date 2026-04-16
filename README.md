# Effective RAG

Effective RAG is a Python backend for document ingestion, OCR, chunking, vector indexing, and document-scoped question answering over WebSockets.

The application receives PDF references from MinIO, extracts each page as an image, runs OCR with `zai-org/GLM-OCR`, stores page-level extraction artifacts back in MinIO, formats the extracted text with an OpenAI-compatible chat API, chunks the generated Markdown with Docling, indexes the chunks in Qdrant, and answers user questions by retrieving and reranking document chunks.

## Features

- Native WebSocket server built with `websockets`
- PDF ingestion from MinIO object storage
- PDF page rendering with PyMuPDF
- OCR with `zai-org/GLM-OCR`
- Page-level JSON extraction artifacts stored in MinIO
- Markdown cleanup and formatting through an OpenAI-compatible chat API
- Markdown chunking with Docling `HybridChunker`
- Embedding generation with Sentence Transformers
- Vector storage and filtered retrieval with Qdrant
- Cross-encoder reranking before answer generation
- Background workers for OCR extraction and formatting/indexing
- Document-scoped search endpoint for RAG-style answers

## Architecture

```text
Client
  -> WebSocket /extraction/ocr
  -> payload: "bucket:path/to/document.pdf"
  -> extraction queue
  -> MinIO PDF download
  -> PDF page rendering
  -> GLM-OCR inference
  -> page JSON artifacts in MinIO
  -> formatting queue
  -> OpenAI-compatible Markdown formatting
  -> Docling Markdown chunking
  -> Sentence Transformer embeddings
  -> Qdrant indexing

Client
  -> WebSocket /search/document
  -> payload: "document_id:user question"
  -> Qdrant filtered vector search
  -> CrossEncoder reranking
  -> OpenAI-compatible answer generation
```

## Tech Stack

- Python 3.11+
- `websockets`
- MinIO
- PyMuPDF
- Pillow
- GLM-OCR / Transformers
- PyTorch
- OpenAI Python client
- Docling
- Sentence Transformers
- Qdrant
- Docker Compose
- `uv`

## Requirements

- Python 3.11 or newer
- `uv`
- Docker and Docker Compose
- A running MinIO instance with the source PDF bucket available
- A MinIO bucket for extraction JSON artifacts
- An OpenAI-compatible chat completions server
- Enough local CPU/GPU memory to load the OCR, embedding, and reranker models

## Configuration

Create a local `.env` file in the project root:

```bash
cp .env.template .env
```

If `.env.template` is not present, create `.env` manually:

```env
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_ENDPOINT=localhost:9000
BUCKET_EXTRATION=

HOST=0.0.0.0
PORT=8000

OPENAI_URL=http://localhost:8080/v1
OPENAI_KEY=sk-no-key-required

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=docling_rag_chunks
QDRANT_REST_PORT=6333
QDRANT_GRPC_PORT=6334

EMBEDDING_MODEL=intfloat/multilingual-e5-small
RERANK_MODEL=
LIMIT_RETRIES_CHUNKS=3
RANGE_UNION_FORMAT_PAGE=2
DEBUG_FORMAT=false
```

### Environment Variables

| Variable | Description |
| --- | --- |
| `MINIO_ACCESS_KEY` | Access key used to connect to MinIO. |
| `MINIO_SECRET_KEY` | Secret key used to connect to MinIO. |
| `MINIO_ENDPOINT` | MinIO endpoint, for example `localhost:9000`. |
| `BUCKET_EXTRATION` | Bucket where extraction JSON artifacts are stored. |
| `HOST` | WebSocket server bind host. Defaults to `0.0.0.0`. |
| `PORT` | WebSocket server port. Defaults to `8000`. |
| `OPENAI_URL` | Base URL for the OpenAI-compatible chat completions API. |
| `OPENAI_KEY` | API key for the OpenAI-compatible chat completions API. |
| `QDRANT_URL` | Qdrant REST URL used by the application. |
| `QDRANT_COLLECTION` | Qdrant collection used for document chunks. |
| `QDRANT_REST_PORT` | Local REST port exposed by Docker Compose. |
| `QDRANT_GRPC_PORT` | Local gRPC port exposed by Docker Compose. |
| `EMBEDDING_MODEL` | Sentence Transformer model used to embed chunks and queries. |
| `RERANK_MODEL` | CrossEncoder model used to rerank retrieved chunks. |
| `LIMIT_RETRIES_CHUNKS` | Maximum number of query refinement attempts during search. |
| `RANGE_UNION_FORMAT_PAGE` | Formatting window size loaded by the service configuration. |
| `DEBUG_FORMAT` | When enabled, writes temporary Markdown/chunk debug files. |

## Getting Started

### 1. Install Dependencies

```bash
uv sync
```

### 2. Start Qdrant

The committed `docker-compose.yml` starts a local Qdrant container:

```bash
docker compose up -d
```

### 3. Run the Application

```bash
uv run python main.py
```

By default, the server listens on:

```text
ws://127.0.0.1:8000
```

## WebSocket API

### OCR Extraction

```text
ws://127.0.0.1:8000/extraction/ocr
```

Send a text message using the following protocol:

```text
bucket:path_document
```

Example:

```text
documents:contracts/project-123.pdf
```

The document ID is derived from the PDF filename without the `.pdf` extension. For example, `contracts/project-123.pdf` becomes `project-123`.

When a valid request is accepted, the server responds with a job-started message and processes the document in the background.

Processing flow:

1. Validate the incoming WebSocket payload.
2. Download the PDF from MinIO.
3. Render each PDF page as an image.
4. Reuse already extracted page artifacts when they exist for the same job ID.
5. Run OCR for missing pages.
6. Store one JSON artifact per extracted page in `BUCKET_EXTRATION`.
7. Format the extracted text as Markdown with the configured LLM endpoint.
8. Chunk the Markdown with Docling.
9. Embed and index chunks in Qdrant under the document ID.

### Document Search

```text
ws://127.0.0.1:8000/search/document
```

Send a text message using the following protocol:

```text
document_id:user question
```

Example:

```text
project-123:What is the project duration?
```

The server searches Qdrant for chunks matching the given `document_id`, reranks the retrieved chunks, asks the configured LLM to produce a final answer, and returns a JSON response:

```json
{
  "document_id": "project-123",
  "query": "What is the project duration?",
  "answer": "..."
}
```

You can also use the included test client:

```bash
uv run python test.py \
  --uri ws://127.0.0.1:8000/search/document \
  --document-id project-123 \
  --question "What is the project duration?"
```

## Project Structure

```text
.
├── core/
│   └── config.py                  # .env loading
├── dto/
│   ├── app_context_dto/           # application context DTO
│   ├── extraction_dto/            # extraction and MinIO DTOs
│   ├── format_extraction_dto/     # formatting queue DTO
│   └── server_config_dto/         # server config DTO
├── models/
│   └── ocr_extraction.py          # GLM-OCR model wrapper
├── processing/
│   └── pdf.py                     # PDF page rendering
├── prompts/
│   ├── format_prompt.py           # Markdown formatting prompt
│   └── init_prompt.py             # search planning and answer prompts
├── routes/
│   ├── extraction.py              # /extraction/ocr WebSocket route
│   └── search.py                  # /search/document WebSocket route
├── services/
│   ├── app_logger.py              # logger factory
│   ├── bucket_minio.py            # MinIO access layer
│   ├── connection_manager.py      # WebSocket connection registry
│   ├── docling_service.py         # Markdown chunking
│   ├── format_service.py          # formatting and indexing worker
│   ├── llm_service.py             # OpenAI-compatible chat client
│   ├── ocr_service.py             # OCR extraction worker
│   ├── qdrant_service.py          # vector indexing and retrieval
│   └── search_service.py          # RAG query loop
├── docker-compose.yml             # local Qdrant service
├── main.py                        # WebSocket server entrypoint
├── pyproject.toml                 # project dependencies
├── run_test.sh                    # sample search client command
└── test.py                        # WebSocket search client
```

## Notes

- The application uses `.env` values directly through `python-dotenv`.
- `BUCKET_EXTRATION` keeps the current project spelling and must match the code.
- Qdrant is created automatically if the configured collection does not exist.
- Source PDFs are not stored by the application; temporary PDF and page image files are removed after processing.
- The OCR model is loaded during application startup through `OcrExtraction`.
- `transformers` is installed from the Hugging Face GitHub repository through `uv`.
- `DEBUG_FORMAT=true` writes local debug files named `tmp.json` and `tmp.md`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
