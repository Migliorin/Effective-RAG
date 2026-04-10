# Effective RAG

Backend service for PDF document ingestion and OCR-oriented preprocessing using native WebSockets.

The current pipeline receives a document reference through a WebSocket connection, downloads the PDF from MinIO, converts each page into an image, and prepares the input for a multimodal OCR stage. The OCR model implementation already exists in the repository, but it is not wired into the application lifecycle yet.

## Overview

Current capabilities:

- WebSocket endpoint for extraction requests
- MinIO-based PDF retrieval
- PDF-to-image page extraction
- application-level logging
- base structure for OCR inference integration

Planned capabilities:

- OCR inference over extracted page images
- structured extraction responses
- persistence layer integration
- automated test coverage for the processing pipeline

## Architecture

```text
Client
  -> WebSocket /extraction/ocr
  -> payload: "bucket:path_document"
  -> MinIO download
  -> PDF page extraction
  -> image artifacts
  -> OCR stage (not enabled yet)
```

## Tech Stack

- Python 3.11+
- WebSockets
- MinIO
- PyMuPDF
- Pillow
- Transformers
- PyTorch
- Docker Compose

## Requirements

- Python 3.11 or newer
- `uv`
- Docker + Docker Compose
- MinIO instance with accessible buckets and PDF objects

## Getting Started

### 1. Environment configuration

Create a local `.env` file:

```bash
cp .env.template .env
```

Configure the required variables:

```env
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_ENDPOINT=
HOST=0.0.0.0
PORT=8000

MONGO_DB_PORT=27017
```

Environment variables:

- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `MINIO_ENDPOINT`: MinIO host and port, for example `localhost:9000`
- `HOST`: interface where the websocket server binds, for example `0.0.0.0`
- `PORT`: websocket server port, for example `8000`
- `MONGO_DB_PORT`: local port exposed by the MongoDB container

### 2. Start local dependencies

The current `docker-compose.yml` provisions MongoDB only:

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
2. downloads the PDF object from MinIO
3. extracts PDF pages into temporary `.png` images
4. emits confirmation and processing logs

Invalid payloads are rejected with a protocol validation message over the WebSocket connection.

## Local Test Client

The repository includes a minimal WebSocket client in [test.py](/Users/lucas/Documents/Projetos/Effective-RAG/test.py):

```bash
uv run python test.py
```

## Project Structure

```text
.
├── core/
│   └── config.py          # environment loading
├── models/
│   └── ocr_extraction.py  # OCR model wrapper
├── processing/
│   └── pdf.py             # PDF page extraction
├── routes/
│   └── extraction.py      # WebSocket route handler and protocol parsing
├── services/
│   ├── app_logger.py      # logger factory
│   ├── bucket_minio.py    # MinIO access layer
│   └── connection_manager.py
├── main.py                # native WebSocket entrypoint
├── docker-compose.yml
├── pyproject.toml
└── test.py
```

## Current Status

The OCR inference layer is implemented in [models/ocr_extraction.py](/Users/lucas/Documents/Projetos/Effective-RAG/models/ocr_extraction.py), using `zai-org/GLM-OCR`, and its initialization is now centralized in [main.py](/home/lumalfa/projetos/Effective-RAG/main.py). The `routes/extraction.py` module keeps the extraction protocol and route handler, while the server lifecycle and route dispatch now live in the native WebSocket entrypoint.

Additional notes:

- temporary files are used for both PDF downloads and generated page images
- logging is configured to `stdout`
- MongoDB is available in local infrastructure but is not integrated into the main processing flow yet
- `transformers` is sourced directly from the Hugging Face GitHub repository in [pyproject.toml](/Users/lucas/Documents/Projetos/Effective-RAG/pyproject.toml)

## License

This project is licensed under the MIT License. See [LICENSE](/Users/lucas/Documents/Projetos/Effective-RAG/LICENSE).
