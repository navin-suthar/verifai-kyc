from __future__ import annotations

from pydantic import BaseModel


class PublicSettings(BaseModel):
    app_name: str
    auto_verify_min_confidence: int
    review_min_confidence: int
    max_upload_bytes: int
    allowed_extensions: list[str]
    llm_enabled: bool
    ollama_model: str
    mock_verification: bool = True
    privacy_notice: str
