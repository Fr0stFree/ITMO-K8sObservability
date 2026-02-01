from pydantic import Field
from pydantic_settings import BaseSettings
import datetime as dt


class ServiceSettings(BaseSettings):
    name: str
    health_check_timeout: dt.timedelta = Field(default=dt.timedelta(seconds=2), alias="HEALTH_CHECK_TIMEOUT")
