from dataclasses import dataclass


@dataclass
class MinioExtractionDto:
    bucket_name: str
    path_extract: str
    content: str
    page: int
    total_pages: int
