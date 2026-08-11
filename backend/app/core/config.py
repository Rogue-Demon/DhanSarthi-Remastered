from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="DhanSarthi API", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    database_url: str = Field(validation_alias="DATABASE_URL")
    database_pool_size: int = Field(default=5, validation_alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, validation_alias="DATABASE_MAX_OVERFLOW")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    cors_origins: str = Field(default="http://localhost:5173", validation_alias="CORS_ORIGINS")
    ai_provider_api_key: str | None = Field(default=None, validation_alias="AI_PROVIDER_API_KEY")
    embedding_provider_api_key: str | None = Field(default=None, validation_alias="EMBEDDING_PROVIDER_API_KEY")
    ai_provider: str = Field(default="mock", validation_alias="AI_PROVIDER")
    ai_model: str = Field(default="meta-llama/Meta-Llama-3-8B-Instruct", validation_alias="AI_MODEL")
    ai_max_tokens: int = Field(default=1024, validation_alias="AI_MAX_TOKENS")
    ai_temperature: float = Field(default=0.2, validation_alias="AI_TEMPERATURE")
    rag_top_k: int = Field(default=5, validation_alias="RAG_TOP_K")
    rag_similarity_threshold: float = Field(default=0.3, validation_alias="RAG_SIMILARITY_THRESHOLD")
    rag_max_context_tokens: int = Field(default=2000, validation_alias="RAG_MAX_CONTEXT_TOKENS")
    rag_chunk_size: int = Field(default=500, validation_alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=50, validation_alias="RAG_CHUNK_OVERLAP")
    embedding_provider: str = Field(default="mock", validation_alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", validation_alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=384, validation_alias="EMBEDDING_DIMENSION")
    storage_bucket: str | None = Field(default=None, validation_alias="STORAGE_BUCKET")
    secret_key: str | None = Field(default=None, validation_alias="SECRET_KEY")
    auth_jwt_secret: str | None = Field(default=None, validation_alias="AUTH_JWT_SECRET")
    auth_jwt_algorithm: str = Field(default="HS256", validation_alias="AUTH_JWT_ALGORITHM")
    auth_access_token_expire_minutes: int = Field(default=30, validation_alias="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
    ai_max_history_messages: int = Field(default=20, validation_alias="AI_MAX_HISTORY_MESSAGES")
    ai_request_timeout_seconds: int = Field(default=60, validation_alias="AI_REQUEST_TIMEOUT_SECONDS")
    ai_max_message_length: int = Field(default=2000, validation_alias="AI_MAX_MESSAGE_LENGTH")
    max_document_size_mb: int = Field(default=10, validation_alias="MAX_DOCUMENT_SIZE_MB")
    document_storage_path: str = Field(default="storage/documents", validation_alias="DOCUMENT_STORAGE_PATH")
    document_max_pages: int = Field(default=100, validation_alias="DOCUMENT_MAX_PAGES")
    document_classification_threshold: float = Field(default=0.6, validation_alias="DOCUMENT_CLASSIFICATION_THRESHOLD")
    dti_threshold_high: float = Field(default=36.0, validation_alias="DTI_THRESHOLD_HIGH")
    dti_threshold_very_high: float = Field(default=50.0, validation_alias="DTI_THRESHOLD_VERY_HIGH")
    emergency_fund_target_months: int = Field(default=6, validation_alias="EMERGENCY_FUND_TARGET_MONTHS")
    emergency_fund_warning_months: int = Field(default=3, validation_alias="EMERGENCY_FUND_WARNING_MONTHS")
    budget_utilization_warning_percent: float = Field(default=85.0, validation_alias="BUDGET_UTILIZATION_WARNING_PERCENT")
    investment_concentration_threshold: float = Field(default=50.0, validation_alias="INVESTMENT_CONCENTRATION_THRESHOLD")

    # Market Data Provider Layer Config
    market_data_provider: str = Field(default="mock", validation_alias="MARKET_DATA_PROVIDER")
    stock_data_api_key: str | None = Field(default=None, validation_alias="STOCK_DATA_API_KEY")
    stock_data_provider: str = Field(default="mock", validation_alias="STOCK_DATA_PROVIDER")
    mutual_fund_provider: str = Field(default="mock", validation_alias="MUTUAL_FUND_PROVIDER")
    fx_provider: str = Field(default="mock", validation_alias="FX_PROVIDER")
    index_provider: str = Field(default="mock", validation_alias="INDEX_PROVIDER")
    interest_rate_provider: str = Field(default="mock", validation_alias="INTEREST_RATE_PROVIDER")
    market_data_cache_ttl_stock: int = Field(default=300, validation_alias="MARKET_DATA_CACHE_TTL_STOCK")
    market_data_cache_ttl_nav: int = Field(default=43200, validation_alias="MARKET_DATA_CACHE_TTL_NAV")
    market_data_cache_ttl_fx: int = Field(default=3600, validation_alias="MARKET_DATA_CACHE_TTL_FX")
    market_data_cache_ttl_index: int = Field(default=300, validation_alias="MARKET_DATA_CACHE_TTL_INDEX")
    market_data_cache_ttl_rate: int = Field(default=86400, validation_alias="MARKET_DATA_CACHE_TTL_RATE")


    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
