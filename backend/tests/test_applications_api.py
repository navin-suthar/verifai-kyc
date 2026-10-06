from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Application


def test_dashboard_summary_counts_match_db(auth_client: TestClient, seeded_db: Session) -> None:
    resp = auth_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()

    total_db = seeded_db.query(Application).count()
    assert body["total_applications"] == total_db
    assert body["verified"] + body["rejected"] + body["needs_review"] + body["pending"] == total_db
    assert 0 <= body["success_rate"] <= 100
    assert len(body["daily_volume"]) == 14
    assert len(body["recent_applications"]) <= 8
    assert all("document_number_masked" in a for a in body["recent_applications"])


def test_list_applications_paginates_and_filters(auth_client: TestClient, seeded_db: Session) -> None:
    resp = auth_client.get("/api/applications", params={"page": 1, "page_size": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1 and body["page_size"] == 5
    assert len(body["items"]) == 5
    assert body["total"] == seeded_db.query(Application).count()

    verified = auth_client.get("/api/applications", params={"status": "verified"}).json()
    assert all(item["status"] == "verified" for item in verified["items"])

    search = auth_client.get("/api/applications", params={"q": "Rahul"}).json()
    assert search["total"] >= 1
    assert any("Rahul" in (i["applicant_name"] or "") for i in search["items"])


def test_list_rejects_invalid_status(auth_client: TestClient) -> None:
    resp = auth_client.get("/api/applications", params={"status": "nope"})
    assert resp.status_code == 422


def test_get_application_detail_never_exposes_raw_number(auth_client: TestClient, seeded_db: Session) -> None:
    app = seeded_db.query(Application).first()
    assert app is not None
    resp = auth_client.get(f"/api/applications/{app.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_id"] == app.customer_id
    assert body["thresholds"]["auto_verify_min"] >= body["thresholds"]["review_min"]
    assert body["verification"]["is_mock"] is True
    assert "document_number_hash" not in body
    assert isinstance(body["fields"], list) and body["fields"]


def test_get_application_404_and_bad_id(auth_client: TestClient) -> None:
    assert auth_client.get("/api/applications/" + "0" * 32).status_code == 404
    assert auth_client.get("/api/applications/not-a-valid-id").status_code == 422
