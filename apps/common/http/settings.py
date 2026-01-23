
from pydantic_settings import BaseSettings


class HTTPServerSettings(BaseSettings):
    port: int = 8000
