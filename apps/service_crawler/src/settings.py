import datetime as dt

from pydantic_settings import BaseSettings


class CrawlerServiceSettings(BaseSettings):
    health_check_timeout: dt.timedelta = dt.timedelta(seconds=2)
