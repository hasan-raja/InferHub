from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    worker_name: str = "worker"
    worker_kind: str = "llm"
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051
    health_host: str = "0.0.0.0"
    health_port: int = 8090
    groq_api_key: str = Field(default="", repr=False)
    groq_base_url: str = "https://api.groq.com"
    groq_timeout_seconds: float = 30.0
    groq_max_retries: int = 2


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
