# Effective RAG

Backend service for PDF ingestion, OCR extraction, and Markdown-oriented text formatting using native WebSockets.

The current pipeline receives a document reference through a WebSocket connection, downloads the PDF from MinIO, converts each page into an image, runs OCR with `zai-org/GLM-OCR`, stores page-level extraction results as JSON in MinIO, and sends the extracted text to an OpenAI-compatible chat server for Markdown formatting.

## Overview

Current capabilities:

- native WebSocket endpoint for OCR extraction requests
- MinIO-based PDF retrieval
- PDF-to-image page extraction
- GLM-OCR image-to-text inference
- page-level JSON persistence in MinIO
- background worker for OCR extraction
- background worker for Markdown formatting
- application-level logging
- Qdrant container configuration for local vector database infrastructure

## Architecture

```text
Client
  -> WebSocket /extraction/ocr
  -> payload: "bucket:path_document"
  -> extraction queue
  -> MinIO PDF download
  -> PDF page extraction
  -> GLM-OCR inference
  -> JSON extraction artifacts in MinIO
  -> formatting queue
  -> OpenAI-compatible Markdown formatting
```

## Tech Stack

- Python 3.11+
- WebSockets
- MinIO
- PyMuPDF
- Pillow
- Transformers
- PyTorch
- OpenAI Python client
- Docker Compose
- Qdrant

## Requirements

- Python 3.11 or newer
- `uv`
- Docker + Docker Compose
- MinIO instance with accessible buckets and PDF objects
- OpenAI-compatible chat server available at the configured endpoint

## Getting Started

### 1. Environment configuration

Create a local `.env` file:

```bash
cp .env.template .env
```

Configure the variables:

```env
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_ENDPOINT=
BUCKET_EXTRATION=

HOST=0.0.0.0
PORT=8000

OPENAI_URL="http://localhost:8080/v1"
OPENAI_KEY="sk-no-key-required"

QDRANT_URL="http://localhost:6333"
QDRANT_COLLECTION="docling_rag_chunks"
QDRANT_REST_PORT=6333
QDRANT_GRPC_PORT=6334

EMBEDDING_MODEL="intfloat/multilingual-e5-small"
```

Environment variables:

- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `MINIO_ENDPOINT`: MinIO host and port, for example `localhost:9000`
- `BUCKET_EXTRATION`: MinIO bucket used to store extraction JSON artifacts
- `HOST`: interface where the websocket server binds, for example `0.0.0.0`
- `PORT`: websocket server port, for example `8000`
- `OPENAI_URL`: OpenAI-compatible chat completions base URL
- `OPENAI_KEY`: API key for the OpenAI-compatible chat server
- `QDRANT_URL`: Qdrant REST endpoint
- `QDRANT_COLLECTION`: Qdrant collection name reserved for local vector data
- `QDRANT_REST_PORT`: local Qdrant REST port exposed by Docker Compose
- `QDRANT_GRPC_PORT`: local Qdrant gRPC port exposed by Docker Compose
- `EMBEDDING_MODEL`: embedding model name reserved for local vector workflows

### 2. Start local dependencies

The committed `docker-compose.yml` provisions Qdrant:

```bash
docker compose up -d
```

### 3. Install Python dependencies

```bash
uv sync
```

### 4. Run the application

```bash
uv run python main.py
```

Default local address:

```text
ws://127.0.0.1:8000
```

## API

### WebSocket endpoint

```text
ws://127.0.0.1:8000/extraction/ocr
```

### Input protocol

The server expects a text payload in the following format:

```text
bucket:path_document
```

Example:

```text
documents:1/f1e4f147-0e55-498a-9ca6-29bd26167ea3.pdf
```

### Processing flow

For each valid request, the service:

1. validates the incoming payload
2. creates an extraction job
3. downloads the PDF object from MinIO
4. extracts PDF pages into temporary `.png` images
5. runs OCR for each page that has not already been extracted for the job
6. stores page extraction JSON files in `BUCKET_EXTRATION`
7. queues the extraction artifacts for Markdown formatting

Invalid payloads are rejected with a protocol validation message over the WebSocket connection.

## Project Structure

```text
.
├── core/
│   └── config.py          # environment loading
├── models/
│   └── ocr_extraction.py  # GLM-OCR model wrapper
├── processing/
│   └── pdf.py             # PDF page extraction
├── routes/
│   └── extraction.py      # WebSocket route handler and protocol parsing
├── services/
│   ├── app_logger.py      # logger factory
│   ├── bucket_minio.py    # MinIO access layer
│   ├── connection_manager.py
│   ├── format_service.py  # Markdown formatting worker
│   └── ocr_service.py     # OCR extraction worker
├── main.py                # native WebSocket entrypoint
├── docker-compose.yml
└── pyproject.toml
```

## Current Status

The server lifecycle and route dispatch live in `main.py`. The `/extraction/ocr` protocol is implemented in `routes/extraction.py`. OCR extraction is handled by `services/ocr_service.py` using `models/ocr_extraction.py`, and Markdown formatting is handled by `services/format_service.py` through an OpenAI-compatible chat completions endpoint.

Additional notes:

- temporary files are used for both PDF downloads and generated page images
- extraction JSON artifacts are stored in MinIO under the configured extraction bucket
- Qdrant is available through Docker Compose, but the main WebSocket processing flow does not query or index it yet
- `transformers` is sourced directly from the Hugging Face GitHub repository in `pyproject.toml`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
