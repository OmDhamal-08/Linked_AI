"""Application configuration loaded from environment variables (.env supported).

Every tunable value lives here so that plans, limits, providers and the
product name can be changed without touching code.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General
    app_name: str = "Linkdine AI"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite:///./linkdine.db"
    auto_create_tables: bool = True
    vector_store: str = "auto"  # auto | pgvector | python

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Auth
    jwt_secret: str = "dev-only-change-me-to-a-long-random-string-32chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    admin_emails: str = ""

    # AI generation
    ai_provider: str = "mock"  # mock | openai | anthropic
    ai_api_key: str = ""
    ai_model: str = "mock-linkdine-v1"
    ai_base_url: str = ""
    ai_timeout_seconds: float = 30.0
    ai_max_output_tokens: int = 900
    ai_temperature: float = 0.7
    ai_input_price_per_1m: float = 0.0
    ai_output_price_per_1m: float = 0.0
    ai_fallback_provider: str = ""
    ai_fallback_api_key: str = ""
    ai_fallback_model: str = ""

    # Embeddings
    embedding_provider: str = "hashing"  # hashing | openai
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 384
    embedding_base_url: str = ""

    # Plans and limits
    free_generations_per_day: int = 3
    free_enhancements_per_day: int = 3
    premium_daily_cap: int = 200
    free_full_post_enabled: bool = False
    premium_max_variations: int = 3
    allow_mock_payments: bool = True

    # RAG
    rag_top_k: int = 5
    rag_candidate_multiplier: int = 4
    rag_weight_vector: float = 0.6
    rag_weight_keyword: float = 0.3
    rag_weight_metadata: float = 0.1

    # Output shaping
    length_short_words: int = 60
    length_medium_words: int = 120
    length_long_words: int = 200
    hashtag_max: int = 5
    max_input_chars: int = 4000
    rate_limit_per_minute: int = 30

    # Ingestion
    ingestion_pii_action: str = "redact"  # redact | reject
    ingestion_max_rows: int = 5000

    # Demo seeding (development only)
    demo_user_email: str = "demo@linkdine.dev"
    demo_user_password: str = "DemoPassword123!"

    @field_validator("ai_provider", "embedding_provider", "vector_store")
    @classmethod
    def _lower(cls, value: str) -> str:
        return value.strip().lower()

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def length_target_words(self, length: str) -> int:
        return {
            "short": self.length_short_words,
            "medium": self.length_medium_words,
            "long": self.length_long_words,
        }.get(length, self.length_medium_words)


@lru_cache
def get_settings() -> Settings:
    return Settings()
