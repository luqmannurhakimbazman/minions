"""Application configuration with environment variable overrides."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "MINIONS_"}

    redis_url: str = "redis://localhost:6379"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    max_retries: int = 3
    worker_concurrency: int = 2
    log_level: str = "INFO"
    container_image: str = "minions-agent:latest"
    container_network_mode: str = "host"


@lru_cache
def get_settings() -> Settings:
    return Settings()
