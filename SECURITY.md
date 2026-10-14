# Security notes for this portfolio repo

## What is intentionally public

- Demo login: `demo.analyst` / `demo-pass-2024` (hardcoded for the portfolio demo)
- Synthetic applicant names and IDs (`SYNTHETIC####`, `DEMO-####-####-####`)
- Placeholder `SECRET_KEY` / Postgres password in `docker-compose.yml` for **local Docker only**

## What is never committed

| Path | Reason |
| --- | --- |
| `.env`, `.env.*`, `**/.env*` | Local secrets / machine config |
| `backend/data/` | SQLite DB + uploaded documents |
| `rag/.qdrant_local/`, `rag/embeddings/cache/` | Local vector / embedding cache |
| `node_modules/`, `.venv/` | Dependencies |

`.env` and `.env.example` are **not** in this repository. Configure overrides with a local `.env` you create yourself, or by exporting environment variables (see README → Configuration reference).

## Before any real deployment

1. Generate a new `SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(48))"`).
2. Change demo credentials and Postgres password.
3. Set `ENVIRONMENT=production`, `COOKIE_SECURE=true`, and a strict `CORS_ORIGINS` list.
4. Never upload real Aadhaar / PAN / passport / bank documents — the privacy guard rejects real-format IDs, but you should not try.

## Reporting

This is a synthetic KYC **demo**. If you find an issue in the demo code, open a GitHub issue on the repository.
