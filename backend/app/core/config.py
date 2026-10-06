"""Application configuration loaded from environment variables / .env.

Every tunable (thresholds, limits, model names) lives here so behaviour can be
changed without touching code. Secrets are never defaulted to production values.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---------------------------------------------------------------
    app_name: str = "VerifAI KYC Platform"
    environment: str = Field(default="development", pattern="^(development|test|production)$")
    debug: bool = False
    api_prefix: str = "/api"
    log_level: str = "INFO"

    # --- Security ----------------------------------------------------------
    secret_key: str = Field(
        default="change-me-development-only-secret-key-0123456789",
        min_length=32,
        description="HS256 signing key for session tokens. Override in .env.",
    )
    session_cookie_name: str = "verifai_session"
    session_ttl_minutes: int = 480
    cookie_secure: bool = False  # set True behind HTTPS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    demo_username: str = "demo.analyst"
    demo_password: str = "demo-pass-2024"  # noqa: S105 - documented demo default, override via .env
    demo_display_name: str = "Demo Analyst"
    demo_role: str = "reviewer"

    rate_limit_default: str = "120/minute"
    rate_limit_login: str = "10/minute"
    rate_limit_upload: str = "20/minute"
    rate_limit_assistant: str = "30/minute"

    # --- Database ----------------------------------------------------------
    database_url: str = f"sqlite:///{(BACKEND_ROOT / 'data' / 'verifai.db').as_posix()}"
    db_echo: bool = False

    # --- Document pipeline -------------------------------------------------
    upload_dir: Path = BACKEND_ROOT / "data" / "uploads"
    max_upload_bytes: int = 5 * 1024 * 1024
    allowed_mime_types: list[str] = ["application/pdf", "image/png", "image/jpeg", "text/plain", "application/json"]
    allowed_extensions: list[str] = [".pdf", ".png", ".jpg", ".jpeg", ".txt", ".json"]

    # --- Human-in-the-loop thresholds (0..100) -----------------------------
    auto_verify_min_confidence: int = Field(default=90, ge=0, le=100)
    review_min_confidence: int = Field(default=70, ge=0, le=100)

    # --- Mock verification -------------------------------------------------
    mock_verification_latency_ms: int = 150
    mock_verification_seed: int = 42

    # --- LLM (Ollama) ------------------------------------------------------
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.6"
    ollama_timeout_seconds: float = 120.0
    llm_enabled: bool = True
    llm_temperature: float = 0.1
    llm_max_tokens: int = 700

    # --- RAG ---------------------------------------------------------------
    qdrant_url: str | None = None  # e.g. http://localhost:6333 ; None => embedded local mode
    qdrant_local_path: Path = PROJECT_ROOT / "rag" / ".qdrant_local"
    qdrant_collection: str = "kyc_policies"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: Path = PROJECT_ROOT / "rag" / "embeddings" / "cache"
    rag_documents_dir: Path = PROJECT_ROOT / "rag" / "documents"
    rag_chunk_size: int = 700
    rag_chunk_overlap: int = 120
    rag_top_k: int = 5
    rag_min_score: float = 0.35

    @field_validator("cors_origins", "allowed_mime_types", "allowed_extensions", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @field_validator("review_min_confidence")
    @classmethod
    def _review_below_auto(cls, value: int, info) -> int:  # noqa: ANN001
        auto = info.data.get("auto_verify_min_confidence")
        if auto is not None and value > auto:
            raise ValueError("review_min_confidence must be <= auto_verify_min_confidence")
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production and settings.secret_key.startswith("change-me"):
        raise RuntimeError("SECRET_KEY must be set in production")
    return settings
