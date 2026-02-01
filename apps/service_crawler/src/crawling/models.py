from dataclasses import dataclass
from enum import StrEnum


class ResourceStatus(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


@dataclass
class CrawledURL:
    url: str
    status: ResourceStatus
    updated_at: str
    comment: str | None = None
