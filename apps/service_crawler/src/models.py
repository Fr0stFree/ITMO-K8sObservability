from dataclasses import dataclass
from typing import Literal

import datetime as dt


@dataclass
class CrawledURL:
    url: str
    status: Literal["UP", "DOWN"]
    updated_at: dt.datetime
