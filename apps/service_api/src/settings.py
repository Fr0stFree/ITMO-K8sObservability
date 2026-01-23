import datetime as dt

from pydantic_settings import BaseSettings


class APIServiceSettings(BaseSettings):
    service_name: str = "APIService"
    health_check_timeout: dt.timedelta = dt.timedelta(seconds=2)
