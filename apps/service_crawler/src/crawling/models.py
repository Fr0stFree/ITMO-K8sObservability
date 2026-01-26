from dataclasses import dataclass
from typing import Literal


@dataclass
class CrawledURL:
    url: str
    status: Literal["UP", "DOWN"]
    updated_at: str
