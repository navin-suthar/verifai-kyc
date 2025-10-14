from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.deps import DbDep, SettingsDep, UserDep, client_ip
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.enums import AuditAction
from app.schemas.assistant import AssistantAskRequest, ChatAnswer
from app.services import application_service, audit_service, document_service, rag_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


def _case_context(app) -> str:  # noqa: ANN001
    field_lines = []
    for f in app.fields or []:
        field_lines.append(
            f"- {f.get('label')}: {f.get('value')!r} (confidence={f.get('confidence')}%, source={f.get('source')})"
        )
    validation_lines = []
    for c in app.validation or []:
        mark = "PASS" if c.get("passed") else "FAIL"
        validation_lines.append(
            f"- [{mark}] {c.get('rule_id')} {c.get('name')} ({c.get('severity')}): {c.get('message')}"
        )
    ver = app.verification
    verification_block = "none"
    if ver is not None:
        verification_block = (
            f"provider={ver.provider}; status={ver.status.value}; "
            f"match_score={ver.match_score}; message={ver.message}; is_mock={ver.is_mock}"
        )
    thresholds = app.thresholds or {}
    excerpt = ""
    if app.document and app.document.extracted_text:
        excerpt = app.document.extracted_text[:800]
    return (
        f"customer_id: {app.customer_id}\n"
        f"applicant_name: {app.applicant_name}\n"
        f"document_type: {app.document_type.value}\n"
        f"document_number_masked: {app.document_number_masked}\n"
        f"status: {app.status.value}\n"
        f"overall_confidence: {app.confidence}\n"
        f"decision_reason: {app.decision_reason}\n"
        f"thresholds: auto_verify_min={thresholds.get('auto_verify_min')}, "
        f"review_min={thresholds.get('review_min')}\n"
        f"issues: {app.issues or []}\n"
        f"extracted_fields:\n" + ("\n".join(field_lines) or "- none") + "\n"
        f"validation_results:\n" + ("\n".join(validation_lines) or "- none") + "\n"
        f"mock_verification: {verification_block}\n"
        f"document_excerpt:\n{excerpt or '(no extracted text)'}\n"
        "NOTE: This is synthetic demo data. Verification is MOCK only."
    )


@router.post("/ask", response_model=ChatAnswer)
@limiter.limit(get_settings().rate_limit_assistant)
def ask(
    request: Request,
    response: Response,
    payload: AssistantAskRequest,
    db: DbDep,
    settings: SettingsDep,
    user: UserDep,
) -> ChatAnswer:
    question = document_service.sanitize_text(payload.question, 1000)
    case = None
    if payload.application_id:
        app = application_service.get_application(db, payload.application_id)
        if app is not None:
            case = _case_context(app)
    result = rag_service.answer(settings, question=question, case_context=case)
    audit_service.record(
        db,
        action=AuditAction.ASSISTANT_QUERY,
        entity_type="assistant",
        entity_id=payload.application_id,
        actor=user.username,
        details={"grounded": result["grounded"], "source_count": len(result["sources"]), "q_len": len(question)},
        ip_address=client_ip(request),
        commit=True,
    )
    return ChatAnswer.model_validate(result)
