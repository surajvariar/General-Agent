from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv
from pydantic import SecretStr
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        validate_default=False,
    )
    OLLAMA_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None
    OPEN_ROUTER_MODELS: List[str] | None = []
    HUGGINGFACEHUB_API_TOKEN: SecretStr | None = None
    TAVILY_API_KEY: SecretStr | None = None
    BASE_URL: str | None = None
    LANGFUSE_TRACING_ENABLED: bool = False
    LANGFUSE_BASE_URL: SecretStr | None = None
    LANGFUSE_PUBLIC_KEY: SecretStr | None = None
    LANGFUSE_SECRET_KEY: SecretStr | None = None


settings = Settings()

if settings.LANGFUSE_PUBLIC_KEY:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY.get_secret_value()
if settings.LANGFUSE_SECRET_KEY:
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY.get_secret_value()
if settings.LANGFUSE_BASE_URL:
    os.environ["LANGFUSE_BASE_URL"] = settings.LANGFUSE_BASE_URL.get_secret_value()
