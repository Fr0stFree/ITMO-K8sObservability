from pydantic import Field
from pydantic_settings import BaseSettings


class HTTPServerSettings(BaseSettings):
    port: int = Field(8000, alias="HTTP_SERVER_PORT")
