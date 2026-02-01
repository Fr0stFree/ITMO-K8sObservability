from pydantic import Field
from pydantic_settings import BaseSettings


class APIServiceSettings(BaseSettings):
    crawler_target_address: str = Field("localhost:50051", alias="CRAWLER_TARGET_ADDRESS")
    analyzer_target_address: str = Field("localhost:50052", alias="ANALYZER_TARGET_ADDRESS")
    pagination_default_limit: int = Field(50, alias="PAGINATION_DEFAULT_LIMIT")
    pagination_max_limit: int = Field(100, alias="PAGINATION_MAX_LIMIT")
