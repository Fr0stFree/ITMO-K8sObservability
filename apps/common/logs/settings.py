import logging

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class LoggingSettings(BaseSettings):
    name: str = Field(..., alias="LOG_NAME")
    level: int = Field(logging.INFO, alias="LOG_LEVEL")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", alias="LOG_FORMAT")

    model_config = ConfigDict(populate_by_name=True)