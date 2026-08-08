from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="DhanSarthi API", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    database_url: str = Field(validation_alias="DATABASE_URL")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    cors_origins: str = Field(default="http://localhost:5173", validation_alias="CORS_ORIGINS")
    ai_provider_api_key: str | None = Field(default=None, validation_alias="AI_PROVIDER_API_KEY")
    embedding_provider_api_key: str | None = Field(default=None, validation_alias="EMBEDDING_PROVIDER_API_KEY")
    storage_bucket: str | None = Field(default=None, validation_alias="STORAGE_BUCKET")
    secret_key: str | None = Field(default=None, validation_alias="SECRET_KEY")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
