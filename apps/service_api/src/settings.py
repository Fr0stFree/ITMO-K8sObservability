import datetime as dt

from pydantic import Field
from pydantic_settings import BaseSettings


class APIServiceSettings(BaseSettings):
    service_name: str = Field("APIService", alias="SERVICE_NAME")
    crawler_target_address: str = Field("localhost:50051", alias="CRAWLER_TARGET_ADDRESS")
    analyzer_target_address: str = Field("localhost:50052", alias="ANALYZER_TARGET_ADDRESS")
    health_check_timeout: dt.timedelta = dt.timedelta(seconds=2)
