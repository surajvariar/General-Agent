from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv
from pydantic import SecretStr


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
    HUGGINGFACEHUB_API_TOKEN: SecretStr | None = None
    BASE_URL: str | None = None


settings = Settings()
