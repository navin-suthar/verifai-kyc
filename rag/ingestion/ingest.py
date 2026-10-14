"""Load synthetic KYC policy documents into the local vector store.

Run from the repo root:

    python rag/ingestion/ingest.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.services.rag_service import ingest_policies  # noqa: E402


def main() -> None:
    settings = get_settings()
    count = ingest_policies(settings)
    print(f"Ingested {count} policy chunks from {settings.rag_documents_dir}")


if __name__ == "__main__":
    main()
