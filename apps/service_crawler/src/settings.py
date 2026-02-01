import datetime as dt

from pydantic import Field
from pydantic_settings import BaseSettings


class CrawlerServiceSettings(BaseSettings):
    concurrent_workers: int = Field(default=5, ge=1, le=100, alias="CRAWLER_CONCURRENT_WORKERS")
    worker_request_timeout: dt.timedelta = Field(default=dt.timedelta(seconds=10), alias="CRAWLER_WORKER_REQUEST_TIMEOUT")
    health_check_timeout: dt.timedelta = Field(default=dt.timedelta(seconds=2), alias="CRAWLER_HEALTH_CHECK_TIMEOUT")