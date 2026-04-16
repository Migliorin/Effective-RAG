from dataclasses import dataclass


@dataclass
class FormatExtractionDto:
    job_id: str
    list_extraction: list[str]
