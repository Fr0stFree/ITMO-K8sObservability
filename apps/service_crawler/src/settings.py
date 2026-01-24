import datetime as dt

from pydantic_settings import BaseSettings


class CrawlerServiceSettings(BaseSettings):
    service_name: str = "CrawlerService"
    concurrent_workers: int = 1
    health_check_timeout: dt.timedelta = dt.timedelta(seconds=2)
