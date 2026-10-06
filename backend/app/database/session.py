"""Engine / session factory. Supports PostgreSQL (Docker) and SQLite (local dev, tests)."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def build_engine(database_url: str | None = None, *, echo: bool | None = None) -> Engine:
    settings = get_settings()
    url = database_url or settings.database_url
    kwargs: dict = {"echo": settings.db_echo if echo is None else echo, "pool_pre_ping": True}

    if url.startswith("sqlite"):
        if ":memory:" not in url:
            db_path = url.split("///", 1)[-1]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False}
        from sqlalchemy.pool import StaticPool

        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool

    engine = create_engine(url, **kwargs)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_connection, _record) -> None:  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


engine: Engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
