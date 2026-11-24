import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Integrated OS Performance Analyzer"
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_database: str = "os_performance_analyzer"
    cors_origins: list[str] | str = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    historical_metrics_interval_seconds: float = 5.0
    historical_metrics_collection: str = "system_metrics_history"
    historical_metrics_max_limit: int = 1000
    historical_metrics_default_limit: int = 100

    @field_validator("cors_origins", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            if v.strip().startswith("["):
                return json.loads(v)
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
