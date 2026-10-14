"""Local RAG over synthetic KYC policy documents.

Retrieval uses Qdrant + FastEmbed when available, and a lexical fallback so
tests and offline demos still work. The generator is instructed never to invent
policy that is not present in the retrieved sources.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.services import llm_service

logger = logging.getLogger(__name__)

REFUSAL = (
    "I do not have that information in the KYC policy knowledge base, so I will not invent an answer. "
    "Try asking about document requirements, validation rules, address verification, human review, "
    "or mock verification."
)

ASSISTANT_SYSTEM = """You are the VerifAI KYC Knowledge Assistant for a SYNTHETIC portfolio demo.
Answer from the provided policy excerpts and, when present, the case file.
When a case file is provided, diagnose why the application has its current status:
list the failed/warning validation rules, confidence vs thresholds, and the mock verification outcome.
Do not invent fields, scores, or rules that are not in the case file or policy excerpts.
If neither the policy excerpts nor the case file support the answer, reply exactly with:
I do not have that information in the KYC policy knowledge base, so I will not invent an answer.
Cite the policy document titles you used in plain language.
Mention that verification providers in this product are mocked.
Keep answers concise (4-10 sentences).
"""


@dataclass
class Chunk:
    chunk_id: str
    document: str
    section: str | None
    text: str


@dataclass
class Retrieved:
    chunk: Chunk
    score: float


_CACHE: dict[str, list[Chunk]] = {}


def _split_sections(markdown: str) -> list[tuple[str | None, str]]:
    parts = re.split(r"(?m)^#{1,3} ", markdown)
    headings = re.findall(r"(?m)^#{1,3} (.+)$", markdown)
    if len(parts) <= 1:
        return [(None, markdown.strip())]
    out: list[tuple[str | None, str]] = []
    preamble = parts[0].strip()
    if preamble:
        out.append((None, preamble))
    for heading, body in zip(headings, parts[1:], strict=False):
        text = body.strip()
        if text:
            out.append((heading.strip(), text))
    return out


def chunk_document(text: str, *, document: str, size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for section, body in _split_sections(text):
        start = 0
        cleaned = re.sub(r"\n{3,}", "\n\n", body).strip()
        if len(cleaned) <= size:
            digest = hashlib.sha256(f"{document}:{section}:{cleaned}".encode()).hexdigest()[:16]
            chunks.append(Chunk(chunk_id=digest, document=document, section=section, text=cleaned))
            continue
        while start < len(cleaned):
            piece = cleaned[start : start + size].strip()
            if piece:
                digest = hashlib.sha256(f"{document}:{section}:{start}:{piece}".encode()).hexdigest()[:16]
                chunks.append(Chunk(chunk_id=digest, document=document, section=section, text=piece))
            start += max(size - overlap, 1)
    return chunks


def load_policy_chunks(settings: Settings) -> list[Chunk]:
    key = str(settings.rag_documents_dir)
    if key in _CACHE:
        return _CACHE[key]
    folder = settings.rag_documents_dir
    chunks: list[Chunk] = []
    if folder.exists():
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            chunks.extend(
                chunk_document(
                    text,
                    document=path.stem.replace("_", " ").title(),
                    size=settings.rag_chunk_size,
                    overlap=settings.rag_chunk_overlap,
                )
            )
    _CACHE[key] = chunks
    return chunks


_STOP = {
    "the",
    "and",
    "for",
    "this",
    "that",
    "with",
    "from",
    "are",
    "was",
    "what",
    "when",
    "why",
    "how",
    "does",
    "application",
    "document",
    "required",
}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}", text.lower()) if t not in _STOP}


def lexical_retrieve(chunks: list[Chunk], query: str, *, top_k: int) -> list[Retrieved]:
    q = _tokens(query)
    if not q:
        return []
    scored: list[Retrieved] = []
    for chunk in chunks:
        overlap = q & _tokens(chunk.text + " " + (chunk.section or "") + " " + chunk.document)
        if not overlap:
            continue
        score = len(overlap) / max(len(q), 1)
        scored.append(Retrieved(chunk=chunk, score=round(score, 4)))
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:top_k]


def _embed_retrieve(settings: Settings, chunks: list[Chunk], query: str) -> list[Retrieved] | None:
    if not chunks:
        return []
    try:
        from fastembed import TextEmbedding
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams
    except ImportError:
        logger.info("qdrant/fastembed not installed; using lexical retrieval")
        return None

    try:
        settings.embedding_cache_dir.mkdir(parents=True, exist_ok=True)
        model = TextEmbedding(model_name=settings.embedding_model, cache_dir=str(settings.embedding_cache_dir))
        query_vec = list(next(model.embed([query])))

        if settings.qdrant_url:
            client = QdrantClient(url=settings.qdrant_url)
        else:
            settings.qdrant_local_path.mkdir(parents=True, exist_ok=True)
            client = QdrantClient(path=str(settings.qdrant_local_path))

        collection = settings.qdrant_collection
        if not client.collection_exists(collection):
            client.create_collection(
                collection, vectors_config=VectorParams(size=len(query_vec), distance=Distance.COSINE)
            )
            vectors = list(model.embed([c.text for c in chunks]))
            points = [
                PointStruct(
                    id=i,
                    vector=list(vec),
                    payload={
                        "chunk_id": c.chunk_id,
                        "document": c.document,
                        "section": c.section,
                        "text": c.text,
                    },
                )
                for i, (c, vec) in enumerate(zip(chunks, vectors, strict=True))
            ]
            client.upsert(collection_name=collection, points=points)

        try:
            hits = client.query_points(collection_name=collection, query=query_vec, limit=settings.rag_top_k).points
        except AttributeError:
            hits = client.search(collection_name=collection, query_vector=query_vec, limit=settings.rag_top_k)

        retrieved: list[Retrieved] = []
        by_id = {c.chunk_id: c for c in chunks}
        for hit in hits:
            payload = hit.payload or {}
            chunk = by_id.get(str(payload.get("chunk_id")))
            if chunk is None:
                chunk = Chunk(
                    chunk_id=str(payload.get("chunk_id") or hit.id),
                    document=str(payload.get("document") or "Policy"),
                    section=payload.get("section"),
                    text=str(payload.get("text") or ""),
                )
            retrieved.append(Retrieved(chunk=chunk, score=float(hit.score or 0)))
        return retrieved
    except Exception as exc:  # noqa: BLE001
        logger.info("vector retrieval unavailable (%s); using lexical fallback", exc.__class__.__name__)
        return None


def retrieve(settings: Settings, question: str) -> list[Retrieved]:
    chunks = load_policy_chunks(settings)
    embedded = _embed_retrieve(settings, chunks, question)
    if embedded is not None:
        return [r for r in embedded if r.score >= settings.rag_min_score][: settings.rag_top_k]
    return [r for r in lexical_retrieve(chunks, question, top_k=settings.rag_top_k) if r.score >= 0.28]


def ingest_policies(settings: Settings) -> int:
    _CACHE.pop(str(settings.rag_documents_dir), None)
    chunks = load_policy_chunks(settings)
    if not chunks:
        return 0
    # Force (re)create the collection when vector stack is available.
    if settings.qdrant_url:
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(url=settings.qdrant_url)
            if client.collection_exists(settings.qdrant_collection):
                client.delete_collection(settings.qdrant_collection)
        except Exception as exc:  # noqa: BLE001
            logger.info("qdrant ingest skipped: %s", exc)
            return len(chunks)
    _embed_retrieve(settings, chunks, "kyc policy")
    return len(chunks)


def answer(
    settings: Settings,
    *,
    question: str,
    case_context: str | None = None,
) -> dict:
    started = time.perf_counter()
    hits = _retrieve_for_question(settings, question, case_context)
    sources = [
        {
            "document": h.chunk.document,
            "section": h.chunk.section,
            "chunk_id": h.chunk.chunk_id,
            "score": h.score,
            "excerpt": h.chunk.text[:360],
        }
        for h in hits
    ]
    # Case diagnosis can still be answered from the case file even if retrieval is thin.
    if not hits and not case_context:
        return {
            "answer": REFUSAL,
            "sources": [],
            "grounded": False,
            "model": "none",
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }

    context = "\n\n".join(
        f"Source: {h.chunk.document}" + (f" / {h.chunk.section}" if h.chunk.section else "") + f"\n{h.chunk.text}"
        for h in hits
    ) or "(no policy chunks retrieved)"
    prompt = f"Policy excerpts:\n{context}\n\n"
    if case_context:
        prompt += f"Case file (synthetic):\n{case_context}\n\n"
    prompt += f"Question: {question}\nAnswer:"

    if settings.llm_enabled:
        try:
            text, llm_ms = llm_service.generate(settings, prompt=prompt, system=ASSISTANT_SYSTEM)
            return {
                "answer": text,
                "sources": sources,
                "grounded": True,
                "model": settings.ollama_model,
                "latency_ms": llm_ms or int((time.perf_counter() - started) * 1000),
            }
        except llm_service.LLMError:
            logger.info("assistant falling back to extractive answer")

    extractive = _extractive_answer(hits, question, case_context=case_context)
    return {
        "answer": extractive,
        "sources": sources,
        "grounded": True,
        "model": "extractive-fallback",
        "latency_ms": int((time.perf_counter() - started) * 1000),
    }


def _retrieve_for_question(settings: Settings, question: str, case_context: str | None) -> list[Retrieved]:
    hits = retrieve(settings, question)
    if case_context:
        # Also retrieve policy for the diagnosis themes present in the case.
        themes = []
        lower = case_context.lower()
        if "needs_review" in lower or "human review" in lower:
            themes.append("human review confidence thresholds validation")
        if "address" in lower or "addr-001" in lower:
            themes.append("address verification completeness postal code")
        if "mismatch" in lower or "mock_verification" in lower:
            themes.append("mock verification partial match")
        if "rejected" in lower:
            themes.append("rejected application investigation floor")
        if "pii" in lower or "real-format" in lower:
            themes.append("privacy guard real PAN Aadhaar")
        for theme in themes:
            for hit in retrieve(settings, theme):
                if all(h.chunk.chunk_id != hit.chunk.chunk_id for h in hits):
                    hits.append(hit)
        hits.sort(key=lambda r: r.score, reverse=True)
        hits = hits[: max(settings.rag_top_k, 5)]
    return hits


def _extractive_answer(hits: list[Retrieved], question: str, *, case_context: str | None = None) -> str:
    parts: list[str] = []
    if case_context:
        status = _case_line(case_context, "status")
        reason = _case_line(case_context, "decision_reason")
        confidence = _case_line(case_context, "overall_confidence")
        issues = _case_line(case_context, "issues")
        verification = _case_line(case_context, "mock_verification")
        parts.append(
            "Case diagnosis (from the linked application file):\n"
            f"- Status: {status or 'unknown'}\n"
            f"- Overall confidence: {confidence or 'n/a'}\n"
            f"- Decision reason: {reason or 'n/a'}\n"
            f"- Issues: {issues or 'none listed'}\n"
            f"- Mock verification: {verification or 'n/a'}"
        )
    if hits:
        top = hits[0].chunk
        title = top.document + (f" — {top.section}" if top.section else "")
        snippet = top.text.split("\n\n")[0][:500]
        parts.append(f"According to {title}: {snippet}")
    elif not case_context:
        return REFUSAL
    parts.append(
        "This answer combines the linked synthetic case file with the local KYC policy knowledge base. "
        "Verification in this demo is performed by a mock service only."
    )
    return "\n\n".join(parts)


def _case_line(case_context: str, key: str) -> str | None:
    prefix = f"{key}:"
    for line in case_context.splitlines():
        if line.lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def policy_dir_ready(path: Path) -> bool:
    return path.exists() and any(path.glob("*.md"))
