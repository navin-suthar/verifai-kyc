from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Application


def test_mock_verify_pan_is_labelled_mock(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/verify/pan",
        json={"name": "Rahul Sharma", "document_number": "SYNTHETIC1234", "date_of_birth": "1989-04-12"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["isMock"] is True
    assert body["status"] == "verified"
    assert body["matchScore"] >= 90
    assert "mock" in body["message"].lower() or "matched" in body["message"].lower()


def test_mock_verify_fail_token_not_found(auth_client: TestClient) -> None:
    resp = auth_client.post("/api/verify/document", json={"name": "Unknown", "document_number": "FAIL0000"})
    assert resp.status_code == 200
    assert resp.json()["status"] in {"not_found", "error"}


def test_rate_limited_upload_accepts_response_param(auth_client: TestClient) -> None:
    """Regression: slowapi headers_enabled requires a Response argument or returns 500."""
    content = b"Name: Rahul Sharma\nDate of Birth: 1989-04-12\nDocument Number: SYNTHETIC1234\nAddress: 14 Lotus Lane, Demo Nagar, Mumbai 400001\n"
    resp = auth_client.post("/api/applications", files={"file": ("rahul.txt", content, "text/plain")})
    assert resp.status_code == 201, resp.text
    assert "response must be" not in resp.text.lower()


def test_upload_synthetic_txt_creates_application(auth_client: TestClient, db: Session) -> None:
    content = (
        b"Name: Rahul Sharma\nDate of Birth: 1989-04-12\nDocument Type: Synthetic PAN\n"
        b"Document Number: SYNTHETIC1234\nAddress: 14 Lotus Lane, Demo Nagar, Mumbai 400001\n"
    )
    resp = auth_client.post("/api/applications", files={"file": ("rahul.txt", content, "text/plain")})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["customer_id"].startswith("DEMO-")
    assert body["status"] in {"verified", "needs_review"}
    assert body["verification"]["is_mock"] is True
    assert "document_number_hash" not in body
    stored = db.get(Application, body["id"])
    assert stored is not None
    assert stored.customer_id == body["customer_id"]


def test_upload_rejects_real_pan_pattern(auth_client: TestClient) -> None:
    content = b"Name: Real Person\nDate of Birth: 1980-01-01\nPAN: ABCDE1234F\n"
    resp = auth_client.post("/api/applications", files={"file": ("bad.txt", content, "text/plain")})
    assert resp.status_code == 400
    assert "real" in resp.json()["detail"].lower() or "PAN" in resp.json()["detail"]


def test_upload_rejects_disallowed_extension(auth_client: TestClient) -> None:
    resp = auth_client.post("/api/applications", files={"file": ("malware.exe", b"MZ", "application/octet-stream")})
    assert resp.status_code == 400


def test_review_approve_flow(auth_client: TestClient) -> None:
    content = (
        b"Name: Aarav Mehta\nDate of Birth: 1985-07-28\nDocument Type: Synthetic Passport\n"
        b"Document Number: SYNP2048811\nAddress: 221 Example Street, Mock City\n"
    )
    created = auth_client.post("/api/applications", files={"file": ("addr.txt", content, "text/plain")})
    assert created.status_code == 201, created.text
    app_id = created.json()["id"]
    if created.json()["status"] != "needs_review":
        return
    reviewed = auth_client.post(f"/api/applications/{app_id}/review", json={"decision": "approve", "notes": "Address confirmed."})
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "verified"
    assert reviewed.json()["review"]["decision"] == "approve"
