# VerifAI — AI-Powered KYC Document Intelligence

Portfolio demo of a **human-in-the-loop KYC verification platform**.

A React analyst console talks to a FastAPI pipeline that extracts fields from **synthetic** identity documents, scores them, applies deterministic rules, calls a **local mock registry**, and (optionally) explains the outcome with a local LLM. A grounded RAG assistant answers policy questions from markdown knowledge-base files stored in Qdrant.

> **This is not a production KYC system.**  
> Do **not** upload real Aadhaar, PAN, passport, bank or any other personal documents.  
> Every applicant, address and identifier in this repository is invented.  
> `POST /api/verify/*` is a **MOCK** service. It never contacts a government or bureau API.

---

## Problem

Manual KYC review is slow, inconsistent and hard to audit. “AI KYC” demos often hide the decision: a black-box model says *verified* without showing extracted fields, rules, evidence or a path for a human to override it.

## Solution

VerifAI makes the pipeline inspectable:

1. Upload a synthetic document (TXT / JSON / PDF / image).
2. Extract name, date of birth, synthetic ID, address and document type.
3. Run a published rule engine (format, age, mandatory fields, privacy guard, address).
4. Call a **mock** verification provider and record the match score.
5. Apply configurable confidence thresholds (auto-verify / human review / reject).
6. Generate an explanation (Ollama `llama3.2-vision` when available, template fallback otherwise).
7. Persist an append-only audit trail.
8. Let analysts ask policy questions with **source citations**.

---

## Architecture

```
React (Vite + TypeScript)
   |
   | REST API  (httpOnly session cookie + CSRF header)
   ↓
FastAPI
   |
   +---- Document Processing      (type sniffing, text/JSON/PDF extract, privacy guard)
   +---- Validation Engine        (deterministic rules)
   +---- Mock KYC Verification    (POST /api/verify/pan|aadhaar|document)
   +---- Decisioning              (configurable HITL thresholds)
   +---- RAG Service
   |        +---- local embeddings (FastEmbed / BGE) or lexical fallback
   |        +---- Qdrant (Docker or embedded)
   |        +---- Ollama / llama3.2-vision on the host
   +---- PostgreSQL (Docker) or SQLite (zero-infra local)
   +---- Audit Logs
```

---

## AI pipeline

| Step | What happens | Where |
| --- | --- | --- |
| 1. Ingest | File type, size and magic-bytes checks. Real PAN / 12-digit ID shapes are rejected. | `document_service` |
| 2. Extract | JSON keys or regex over text. Images are accepted for preview; TXT/JSON/PDF are the reliable demo path. | `document_service` |
| 3. Validate | REQ / NAME / DOB / FMT / PII / ADDR / TYPE rules. | `validation_service` |
| 4. Mock verify | Deterministic local registry. Always labelled `isMock: true`. | `verification_service` |
| 5. Decide | `confidence ≥ AUTO_VERIFY_MIN` + clean rules + mock match → Verified. Review band → human. Below floor → reject / investigate. | `decision_service` |
| 6. Explain | Ollama `llama3.2-vision` (configurable) or a template if the daemon is down. | `llm_service` |
| 7. Audit | Upload, extract, validate, verify, decide, review, assistant queries. | `audit_service` |

Thresholds (change without code):

```
AUTO_VERIFY_MIN_CONFIDENCE=90
REVIEW_MIN_CONFIDENCE=70
```

---

## RAG pipeline

1. Load markdown policies from `rag/documents/`.
2. Split on headings, then chunk (~700 chars, 120 overlap).
3. Embed locally with FastEmbed (`BAAI/bge-small-en-v1.5`) when the optional `ai` extra is installed.
4. Upsert into Qdrant (`kyc_policies`).
5. Retrieve top-k chunks above a score floor.
6. Send excerpts + optional case file to Ollama.
7. **Refuse** when nothing relevant is retrieved — the model is not allowed to invent policy.

If Qdrant or the embedding model is unavailable, a lexical retriever keeps the assistant usable for demos and tests.

Re-ingest:

```bash
python rag/ingestion/ingest.py
```

---

## Technology choices

| Choice | Why |
| --- | --- |
| React + TypeScript + Vite | Typed SPA, fast local loop, feature-folder architecture. |
| Tailwind CSS v4 | Enterprise dashboard tokens (light/dark) without a heavy design system. |
| FastAPI + Pydantic | OpenAPI, validation, dependency-injected settings. |
| SQLAlchemy 2 + PostgreSQL / SQLite | Same models in Docker and laptop-only mode. |
| Ollama + llama3.2-vision | Local multimodal LLM, no paid API, EU-friendly “data stays on the machine” story. |
| Qdrant + FastEmbed | Local vector search without a cloud embedding vendor. |
| Mock verification | Honest about not calling UIDAI / NSDL. |
| httpOnly cookie + CSRF header | Portfolio-grade session handling (no tokens in `localStorage`). |

---

## Security (portfolio-level)

- Synthetic data only; privacy guard rejects real-format PAN / Aadhaar-like numbers.
- Upload allow-list (extension + sniffed MIME), 5 MB cap, path-safe filenames.
- Session JWT in an httpOnly `SameSite=lax` cookie; mutating cookie calls require `X-Requested-With`.
- Rate limits on login, upload and assistant.
- **No `.env` / `.env.example` files are committed.** Configure via shell env or a local `.env` you create yourself (gitignored).
- Uploaded files and SQLite DBs under `backend/data/` are gitignored — never publish real KYC scans.
- Audit log scrubs obvious sensitive keys; document numbers are stored masked + salted hash.
- Security headers on every response; CORS is an explicit origin list.
- Assistant is retrieval-grounded and refuses when the knowledge base has no answer.

---

## Configuration reference

Create a local `.env` in the repo root if you want to override defaults (optional for SQLite demo).  
**Do not commit this file.**

| Variable | Default (dev) | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | change-me… | JWT signing key — generate a new one before any public deploy |
| `DEMO_USERNAME` / `DEMO_PASSWORD` | `demo.analyst` / `demo-pass-2024` | Single demo account |
| `DATABASE_URL` | SQLite under `backend/data/` | Or PostgreSQL URL with Docker |
| `AUTO_VERIFY_MIN_CONFIDENCE` | `90` | Auto-verify band |
| `REVIEW_MIN_CONFIDENCE` | `70` | Human-review band |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local LLM |
| `OLLAMA_MODEL` | `llama3.2-vision` | Model name |
| `LLM_ENABLED` | `true` | Set `false` to use template explanations only |
| `QDRANT_URL` | empty | Empty = lexical / embedded retrieval |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed browser origins |
| `VITE_API_BASE_URL` | `/api` | Frontend API base (Vite proxy) |

Generate a secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Local setup (no Docker)

**Prerequisites:** Python 3.11–3.12, Node 20+, optional [Ollama](https://ollama.com).

```bash
git clone https://github.com/navin-suthar/verifai-kyc.git
cd verifai-kyc
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -e ".[dev]"
python -m app.database.seed
uvicorn app.main:app --reload --port 8000
```

SQLite is the default (`backend/data/verifai.db`) so PostgreSQL is optional.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

**Demo login:** `demo.analyst` / `demo-pass-2024` (pre-filled — portfolio demo only).

### Optional local AI

```bash
ollama pull llama3.2-vision
ollama serve
pip install -e ".[ai]"          # from backend/ — FastEmbed + Qdrant client
python rag/ingestion/ingest.py  # from repo root, PYTHONPATH=backend
```

If Ollama is not running, explanations and the assistant fall back to templates / extractive answers. The rest of the product still works.

### Sample documents

Download from the Upload page, or use:

- `frontend/public/samples/rahul_sharma_synthetic_pan.txt` → typically **Verified**
- `frontend/public/samples/incomplete_address_review.txt` → typically **Needs review**
- `backend/samples/reject_low_confidence.txt` → **Rejected**

---

## Docker

PostgreSQL + Qdrant + API + nginx UI. Ollama remains on the host.

```bash
ollama pull llama3.2-vision && ollama serve
docker compose up --build
```

- UI: [http://localhost:8080](http://localhost:8080)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Tests

```bash
cd backend && pytest
cd frontend && npm test
```

Coverage includes auth/CSRF, application APIs, the validation engine, mock verification, upload privacy guards, RAG refusal, and frontend sanitisation helpers.

---

## Demo script (for interviews)

1. Sign in with the pre-filled demo account. Point out the privacy disclaimer.
2. Dashboard — volumes, success rate, recent synthetic applications.
3. Upload `rahul_sharma_synthetic_pan.txt`. Walk the analysis split view: preview, per-field confidence, rules, **MOCK** registry card, explanation.
4. Open Verification Result. Show the threshold bands.
5. Upload the incomplete-address sample. Use **Approve / Reject / Request more information**.
6. Knowledge Assistant: *“What documents are required for KYC?”* — show citations. Then *“What is the melting point of unobtainium?”* — show the refusal.
7. Audit Logs — the actions you just took.

---

## Project structure

```
frontend/          React + TypeScript dashboard
backend/app/
  api/             FastAPI routers
  models/          SQLAlchemy
  schemas/         Pydantic
  services/        document, validation, verification, rag, audit, pipeline
  database/        session + synthetic seed
backend/tests/
rag/documents/     synthetic KYC policies
rag/ingestion/     vector ingest entrypoint
docker-compose.yml
README.md
```

---

## Screenshots (UI reference)

| Screen | What it shows |
| --- | --- |
| Login | Demo sign-in, privacy notice, stack: Ollama · llama3.2-vision · Qdrant · FastAPI · React |
| Dashboard | Totals, verified / rejected / review, charts, recent applications |
| Upload | Dropzone, sample synthetic files, privacy guard |
| Analysis | Document preview, field confidence, validation, **MOCK** verification, **Ask assistant** |
| Knowledge Assistant | Grounded RAG answers with citations / extractive fallback |
| Audit logs | Append-only trail (`assistant.query`, pipeline decisions) — raw IDs never stored |

---

## Future improvements

- Optional on-device OCR (e.g. Tesseract) for image samples.
- Evaluation harness: golden synthetic set → precision/recall of extraction and decisions.
- Multi-reviewer workflow and maker-checker.
- Structured output from llama3.2-vision for image extraction (kept off the critical path so the demo runs offline).
- OpenTelemetry traces around retrieve → generate latency.

---

## Licence / disclaimer

MIT-style portfolio demo. Not affiliated with any government KYC service.  
Do not upload real identity documents. Do not treat mock verification as legal proof of identity.
