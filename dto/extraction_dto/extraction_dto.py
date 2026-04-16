from dataclasses import dataclass


@dataclass
class ExtractionDto:
    job_id: str
    bucket_name: str
    object_name: str
