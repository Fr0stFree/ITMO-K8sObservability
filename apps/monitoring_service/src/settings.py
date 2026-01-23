import datetime as dt

from pydantic_settings import BaseSettings

class MonitoringServiceSettings(BaseSettings):
    health_check_timeout: dt.timedelta = dt.timedelta(seconds=2)
