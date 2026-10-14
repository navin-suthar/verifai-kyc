"""Thin Ollama client used for explanations and the grounded RAG assistant."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


def generate(
    settings: Settings,
    *,
    prompt: str,
    system: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout_seconds: float | None = None,
) -> tuple[str, int]:
    """Call Ollama /api/generate. Returns (text, latency_ms)."""
    if not settings.llm_enabled:
        raise LLMError("LLM is disabled")

    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": settings.llm_temperature if temperature is None else temperature,
            "num_predict": settings.llm_max_tokens if max_tokens is None else max_tokens,
        },
    }
    url = settings.ollama_base_url.rstrip("/") + "/api/generate"
    timeout = timeout_seconds if timeout_seconds is not None else settings.ollama_timeout_seconds
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
            data = response.json() if response.content else {}
            if response.status_code >= 400:
                err = data.get("error") if isinstance(data, dict) else None
                raise LLMError(str(err or f"Ollama HTTP {response.status_code}"))
    except httpx.HTTPError as exc:
        logger.warning("ollama request failed: %s", exc)
        raise LLMError("The local LLM is unavailable") from exc

    if isinstance(data, dict) and data.get("error"):
        raise LLMError(str(data["error"]))

    text = str(data.get("response") or "").strip()
    if not text:
        raise LLMError("The local LLM returned an empty response")
    latency_ms = int(data.get("total_duration", 0) / 1_000_000) if data.get("total_duration") else 0
    return text, latency_ms


def template_explanation(*, status: str, name: str | None, issues: list[str], decision_reason: str) -> str:
    who = name or "the applicant"
    if status == "verified":
        return (
            f"All mandatory fields were extracted and every error-level validation rule passed for {who}. "
            f"{decision_reason} The mock registry returned a match, so the application was verified automatically."
        )
    if status == "needs_review":
        issue_txt = (" Detected issues: " + "; ".join(issues) + ".") if issues else ""
        return (
            f"The pipeline could not auto-approve this application for {who}.{issue_txt} "
            f"{decision_reason} A human reviewer should confirm the extracted fields before a final decision."
        )
    issue_txt = (" Issues: " + "; ".join(issues) + ".") if issues else ""
    return (
        f"The application for {who} was rejected by the automated decisioning rules.{issue_txt} "
        f"{decision_reason} This is a demo outcome produced from synthetic data only."
    )
