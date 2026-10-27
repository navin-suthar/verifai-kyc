from app.core.config import get_settings
from app.services.rag_service import REFUSAL, answer, load_policy_chunks, retrieve


def test_policy_documents_are_chunked() -> None:
    chunks = load_policy_chunks(get_settings())
    assert len(chunks) >= 6
    titles = {c.document.lower() for c in chunks}
    assert any("policy" in t or "kyc" in t for t in titles)


def test_retrieve_address_verification_question() -> None:
    hits = retrieve(get_settings(), "Why does this application require address verification?")
    assert hits
    blob = " ".join(h.chunk.text.lower() + " " + (h.chunk.document.lower()) for h in hits)
    assert "address" in blob


def test_assistant_refuses_when_not_in_knowledge_base() -> None:
    result = answer(get_settings(), question="What is the melting point of unobtainium alloy ZX91?")
    assert result["grounded"] is False
    assert result["answer"] == REFUSAL
    assert result["sources"] == []


def test_assistant_answers_from_policy(auth_client) -> None:  # noqa: ANN001
    resp = auth_client.post("/api/assistant/ask", json={"question": "What documents are required for KYC?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["grounded"] is True
    assert len(body["sources"]) >= 1
    assert "invent" not in body["answer"].lower() or "synthetic" in body["answer"].lower() or "document" in body["answer"].lower()


def test_assistant_uses_linked_application_for_diagnosis(auth_client, seeded_db) -> None:  # noqa: ANN001
    from app.models import Application

    app = seeded_db.query(Application).filter(Application.status == "needs_review").first()
    if app is None:
        app = seeded_db.query(Application).first()
    assert app is not None
    resp = auth_client.post(
        "/api/assistant/ask",
        json={
            "question": f"Diagnose why application {app.customer_id} needs review.",
            "application_id": app.id,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["grounded"] is True
    assert app.customer_id in body["answer"] or "Case diagnosis" in body["answer"] or "confidence" in body["answer"].lower()
