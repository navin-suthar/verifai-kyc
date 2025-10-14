from __future__ import annotations

import os
from collections.abc import Iterator

# Must be set before the app/settings are imported.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-test-secret-key")
os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("QDRANT_URL", "")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import build_engine, get_db
from app.main import create_app


@pytest.fixture(scope="session")
def engine():
    import app.models  # noqa: F401

    eng = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    TestingSession = sessionmaker(
        bind=connection, autoflush=False, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def app(db: Session):
    application = create_app()

    def _override_db() -> Iterator[Session]:
        yield db

    application.dependency_overrides[get_db] = _override_db
    return application


@pytest.fixture()
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_client(client: TestClient) -> TestClient:
    settings = get_settings()
    resp = client.post(
        "/api/auth/login",
        json={"username": settings.demo_username, "password": settings.demo_password},
    )
    assert resp.status_code == 200, resp.text
    client.headers.update({"X-Requested-With": "XMLHttpRequest"})
    return client


@pytest.fixture()
def seeded_db(db: Session) -> Session:
    from app.database.seed import seed

    seed(db)
    return db
