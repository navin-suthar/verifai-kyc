"""Orchestrates extract → validate → mock-verify → decide → explain → audit."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Application, ApplicationStatus, AuditAction, Document, VerificationResult
from app.models.enums import VerificationStatus
from app.schemas.application import ApplicationDetail
from app.services import application_service, audit_service, decision_service, document_service, llm_service
from app.services.document_service import DocumentError
from app.services.validation_service import issues_from, validate_fields
from app.services.verification_service import verify_from_fields

logger = logging.getLogger(__name__)

EXPLAIN_SYSTEM = (
    "You are a KYC decision explainer for a SYNTHETIC demo platform. "
    "Write 2-4 sentences in plain English. Mention that verification is mocked. "
    "Do not invent fields that were not extracted. Do not mention real government APIs."
)


def _store_file(settings: Settings, application_id: str, filename: str, content: bytes) -> Path:
    folder = settings.upload_dir / application_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / document_service.sanitize_filename(filename)
    path.write_bytes(content)
    return path


def process_upload(
    db: Session,
    settings: Settings,
    *,
    content: bytes,
    filename: str,
    declared_type: str | None,
    actor: str,
    ip_address: str | None,
) -> ApplicationDetail:
    try:
        extracted = document_service.extract(content, filename, declared_type, settings)
    except DocumentError:
        audit_service.record(
            db,
            action=AuditAction.DOCUMENT_REJECTED,
            entity_type="document",
            actor=actor,
            details={"filename": document_service.sanitize_filename(filename), "reason": "rejected_upload"},
            ip_address=ip_address,
            commit=True,
        )
        raise

    app = Application(
        customer_id=application_service.next_customer_id(db),
        applicant_name=document_service.field_value(extracted.fields, "full_name"),
        document_type=extracted.document_type,
        document_number_masked=document_service.mask_document_number(
            document_service.field_value(extracted.fields, "document_number")
        ),
        document_number_hash=(
            document_service.hash_document_number(
                document_service.field_value(extracted.fields, "document_number") or "",
                settings.secret_key,
            )
            if document_service.field_value(extracted.fields, "document_number")
            else None
        ),
        status=ApplicationStatus.PROCESSING,
        fields=extracted.fields,
        validation=[],
        issues=[],
        thresholds=decision_service.thresholds_payload(settings),
    )
    db.add(app)
    db.flush()

    stored = _store_file(settings, app.id, filename, content)
    app.document = Document(
        filename=document_service.sanitize_filename(filename),
        mime_type=extracted.mime_type,
        size_bytes=len(content),
        sha256=extracted.sha256,
        storage_path=str(stored),
        extracted_text=extracted.text,
        page_count=extracted.page_count,
    )
    audit_service.record(
        db,
        action=AuditAction.DOCUMENT_UPLOADED,
        entity_type="application",
        entity_id=app.id,
        actor=actor,
        details={"customer_id": app.customer_id, "mime_type": extracted.mime_type, "size_bytes": len(content)},
        ip_address=ip_address,
    )

    run_pipeline(db, settings, app, actor=actor, ip_address=ip_address)
    db.commit()
    db.refresh(app)
    return application_service.to_detail(app, settings)


def run_pipeline(
    db: Session,
    settings: Settings,
    app: Application,
    *,
    actor: str,
    ip_address: str | None = None,
) -> Application:
    fields = list(app.fields or [])
    validation = validate_fields(fields, app.document_type)
    confidence = document_service.overall_confidence(fields)
    verification_payload = verify_from_fields(fields, app.document_type, settings)
    status, reason = decision_service.decide_status(
        confidence=confidence,
        validation=validation,
        verification=verification_payload,
        auto_verify_min=settings.auto_verify_min_confidence,
        review_min=settings.review_min_confidence,
    )
    issues = issues_from(validation)

    app.fields = fields
    app.validation = validation
    app.issues = issues
    app.confidence = confidence
    app.status = status
    app.decision_reason = reason
    app.applicant_name = document_service.field_value(fields, "full_name") or app.applicant_name
    app.document_number_masked = document_service.mask_document_number(
        document_service.field_value(fields, "document_number")
    )
    app.thresholds = decision_service.thresholds_payload(settings)

    if app.verification is None:
        app.verification = VerificationResult(
            provider=verification_payload["provider"],
            status=VerificationStatus(verification_payload["status"]),
            match_score=verification_payload["match_score"],
            message=verification_payload["message"],
            is_mock=True,
            raw_response=verification_payload["raw_response"],
            checked_at=verification_payload["checked_at"],
        )
    else:
        app.verification.provider = verification_payload["provider"]
        app.verification.status = VerificationStatus(verification_payload["status"])
        app.verification.match_score = verification_payload["match_score"]
        app.verification.message = verification_payload["message"]
        app.verification.raw_response = verification_payload["raw_response"]
        app.verification.checked_at = verification_payload["checked_at"]

    app.explanation = _explain(settings, app)

    audit_service.record(
        db,
        action=AuditAction.EXTRACTION_COMPLETED,
        entity_type="application",
        entity_id=app.id,
        actor="pipeline",
        details={"fields": [f.get("name") for f in fields], "confidence": confidence},
        ip_address=ip_address,
    )
    audit_service.record(
        db,
        action=AuditAction.VALIDATION_COMPLETED,
        entity_type="application",
        entity_id=app.id,
        actor="pipeline",
        details={"failed": [c["rule_id"] for c in validation if not c["passed"]]},
        ip_address=ip_address,
    )
    audit_service.record(
        db,
        action=AuditAction.VERIFICATION_COMPLETED,
        entity_type="application",
        entity_id=app.id,
        actor="pipeline",
        details={
            "provider": verification_payload["provider"],
            "status": verification_payload["status"],
            "match_score": verification_payload["match_score"],
            "is_mock": True,
        },
        ip_address=ip_address,
    )
    audit_service.record(
        db,
        action=AuditAction.DECISION_MADE,
        entity_type="application",
        entity_id=app.id,
        actor="pipeline",
        details={"status": status.value, "reason": reason, "actor_user": actor},
        ip_address=ip_address,
    )
    return app


def _explain(settings: Settings, app: Application) -> str:
    fallback = llm_service.template_explanation(
        status=app.status.value,
        name=app.applicant_name,
        issues=list(app.issues or []),
        decision_reason=app.decision_reason or "",
    )
    if not settings.llm_enabled:
        return fallback
    prompt = (
        f"Applicant: {app.applicant_name or 'unknown'}\n"
        f"Document type: {app.document_type.value}\n"
        f"Status: {app.status.value}\n"
        f"Confidence: {app.confidence}\n"
        f"Decision reason: {app.decision_reason}\n"
        f"Issues: {app.issues}\n"
        f"Validation: {app.validation}\n"
        f"Mock verification: {(app.verification.message if app.verification else 'n/a')}\n"
        "Write the explanation now."
    )
    try:
        # Keep upload snappy: if Ollama is slow/unavailable, fall back immediately.
        text, _ = llm_service.generate(
            settings,
            prompt=prompt,
            system=EXPLAIN_SYSTEM,
            max_tokens=280,
            timeout_seconds=min(20.0, settings.ollama_timeout_seconds),
        )
        return text
    except llm_service.LLMError:
        logger.info("using template explanation; ollama unavailable")
        return fallback
