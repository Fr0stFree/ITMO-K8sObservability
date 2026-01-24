from dataclasses import dataclass
import datetime as dt
from typing import Literal


@dataclass
class CrawledURL:
    url: str
    status: Literal["UP", "DOWN"]
    updated_at: dt.datetime
