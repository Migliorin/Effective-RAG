from dataclasses import dataclass


@dataclass(frozen=True)
class ServerConfigDto:
    host: str
    port: int
