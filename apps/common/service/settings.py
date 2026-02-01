import datetime as dt

from pydantic import Field
from pydantic_settings import BaseSettings


class ServiceSettings(BaseSettings):
    name: str
    health_check_timeout: dt.timedelta = Field(default=dt.timedelta(seconds=2), alias="HEALTH_CHECK_TIMEOUT")
