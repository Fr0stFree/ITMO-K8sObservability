import datetime as dt

from pydantic_settings import BaseSettings


class AnalyzerServiceSettings(BaseSettings):
    service_name: str = "AnalyzerService"
    health_check_timeout: dt.timedelta = dt.timedelta(seconds=2)
