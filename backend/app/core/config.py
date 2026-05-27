from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "InferHub"
    app_env: str = "local"
    log_level: str = "INFO"
    api_version: str = "v1"
    api_key_pepper: str = Field(default="change-me-in-local-dev", repr=False)
    default_free_rpm: int = 30
    default_enterprise_rpm: int = 600
    default_admin_rpm: int = 1200
    request_body_limit_bytes: int = 10 * 1024 * 1024

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "inferhub"
    postgres_user: str = "inferhub"
    postgres_password: str = "inferhub"

    redis_url: str = "redis://localhost:6379/0"

    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "inferhub"
    clickhouse_user: str = "inferhub"
    clickhouse_password: str = "inferhub"

    kafka_bootstrap_servers: str = "localhost:9092"

    groq_api_key: str = Field(default="", repr=False)
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_timeout_seconds: float = 30.0

    floci_endpoint_url: str = "http://localhost:4566"
    floci_region: str = "us-east-1"
    floci_access_key_id: str = "inferhub"
    floci_secret_access_key: str = Field(default="inferhub-local", repr=False)
    s3_bucket_model_artifacts: str = "inferhub-model-artifacts"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def clickhouse_url(self) -> str:
        return f"http://{self.clickhouse_host}:{self.clickhouse_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
