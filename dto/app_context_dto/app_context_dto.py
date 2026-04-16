from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Optional

@dataclass
class AppContextDto:
    logger: object
    queue: Queue
    queue_format: Queue
    connection_manager: object
    ocr_service: object
    format_service: object
    qdrant_service: object
    llm_service: object
    search_service: object
    worker_thread: Optional[Thread]
    worker_thread_format: Optional[Thread]
