"""Upload hygiene, text extraction and field extraction for synthetic KYC files.

Real-world identity patterns (PAN / Aadhaar style) are rejected so this demo
cannot be used to process genuine personal documents.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

from app.core.config import Settings
from app.models.enums import DocumentType, FieldSource

logger = logging.getLogger(__name__)

MAX_EXTRACTED_CHARS = 50_000
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Real-world patterns we refuse to ingest. Synthetic IDs use different formats.
REAL_PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
REAL_AADHAAR = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
HTML_OR_SCRIPT = re.compile(r"<\s*(script|html|iframe|object|embed)\b", re.I)

# Synthetic formats used throughout the demo.
SYNTHETIC_PAN = re.compile(r"\bSYNTHETIC\d{4}\b", re.I)
SYNTHETIC_NATIONAL = re.compile(r"\bDEMO-\d{4}-\d{4}-\d{4}\b", re.I)
SYNTHETIC_PASSPORT = re.compile(r"\bSYNP\d{7}\b", re.I)
SYNTHETIC_UTILITY = re.compile(r"\bACC-DEMO-\d{6}\b", re.I)

NAME_RE = re.compile(r"(?:full\s*)?name\s*[:\-]\s*(.+)", re.I)
DOB_RE = re.compile(r"(?:date\s*of\s*birth|dob|born)\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}[/-][0-9]{2}[/-][0-9]{4})", re.I)
NUMBER_RE = re.compile(
    r"(?:document\s*number|doc(?:ument)?\s*no\.?|pan|passport|id(?:entifier)?)\s*[:\-]\s*([A-Z0-9-]{6,32})",
    re.I,
)
ADDRESS_RE = re.compile(r"address\s*[:\-]\s*(.+)", re.I)
TYPE_RE = re.compile(r"document\s*type\s*[:\-]\s*(.+)", re.I)

MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_PDF = b"%PDF"

JSON_NAME_KEYS = ("name", "full_name", "fullName", "applicant_name", "applicantName")
JSON_DOB_KEYS = ("date_of_birth", "dateOfBirth", "dob")
JSON_NUMBER_KEYS = ("document_number", "documentNumber", "pan", "id", "passport")
JSON_ADDRESS_KEYS = ("address",)
JSON_TYPE_KEYS = ("document_type", "documentType", "type")


class DocumentError(ValueError):
    """Raised for rejected uploads (type, size, privacy, sanitisation)."""


@dataclass
class ExtractionResult:
    text: str
    mime_type: str
    page_count: int | None
    document_type: DocumentType
    fields: list[dict]
    sha256: str


def sanitize_filename(name: str) -> str:
    cleaned = unicodedata.normalize("NFKC", name or "document")
    cleaned = Path(cleaned).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", cleaned)
    return (cleaned or "document")[:80]


def sanitize_text(value: str, max_length: int = MAX_EXTRACTED_CHARS) -> str:
    value = CONTROL_CHARS.sub("", value)
    value = HTML_OR_SCRIPT.sub("", value)
    return value.strip()[:max_length]


def sniff_mime(content: bytes, filename: str, declared: str | None) -> str:
    if content.startswith(MAGIC_PDF):
        return "application/pdf"
    if content.startswith(MAGIC_PNG):
        return "image/png"
    if content.startswith(MAGIC_JPEG):
        return "image/jpeg"
    stripped = content.lstrip()
    if stripped.startswith((b"{", b"[")):
        return "application/json"
    suffix = Path(filename).suffix.lower()
    mapping = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".json": "application/json",
        ".txt": "text/plain",
    }
    if suffix in mapping:
        return mapping[suffix]
    if declared in mapping.values():
        return declared
    return "application/octet-stream"


def validate_upload(content: bytes, filename: str, declared_type: str | None, settings: Settings) -> str:
    if not content:
        raise DocumentError("The uploaded file is empty.")
    if len(content) > settings.max_upload_bytes:
        raise DocumentError(f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit.")

    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise DocumentError(f"File type '{suffix or 'unknown'}' is not allowed.")

    mime = sniff_mime(content, filename, declared_type)
    if mime not in settings.allowed_mime_types:
        raise DocumentError(f"Detected type '{mime}' is not allowed.")

    if mime in {"image/png", "image/jpeg"}:
        try:
            from PIL import Image

            with Image.open(BytesIO(content)) as img:
                img.verify()
        except Exception as exc:  # noqa: BLE001
            raise DocumentError("Image file could not be decoded.") from exc

    return mime


def contains_real_identity_pattern(text: str) -> str | None:
    """Return a human-readable reason if the payload looks like a real ID."""
    if REAL_PAN.search(text):
        return "A real-format PAN-like identifier was detected. Only synthetic IDs (e.g. SYNTHETIC1234) are accepted."
    # Ignore DEMO-####-####-#### which is our synthetic national ID.
    stripped = SYNTHETIC_NATIONAL.sub("", text)
    if REAL_AADHAAR.search(stripped):
        return "A 12-digit Aadhaar-like number was detected. Do not upload real identity documents."
    return None


def extract_text(content: bytes, mime_type: str) -> tuple[str, int | None]:
    if mime_type == "application/pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return sanitize_text("\n".join(pages)), len(reader.pages)
    if mime_type in {"text/plain", "application/json"}:
        return sanitize_text(content.decode("utf-8", errors="replace")), 1
    if mime_type in {"image/png", "image/jpeg"}:
        return "", 1
    raise DocumentError(f"Unsupported media type: {mime_type}")


def detect_document_type(text: str, hint: str | None = None) -> DocumentType:
    blob = f"{hint or ''} {text}".lower()
    if "synthetic_pan" in blob or "synthetic pan" in blob or SYNTHETIC_PAN.search(text):
        return DocumentType.SYNTHETIC_PAN
    if "national" in blob or SYNTHETIC_NATIONAL.search(text):
        return DocumentType.SYNTHETIC_NATIONAL_ID
    if "passport" in blob or SYNTHETIC_PASSPORT.search(text):
        return DocumentType.SYNTHETIC_PASSPORT
    if "utility" in blob or SYNTHETIC_UTILITY.search(text):
        return DocumentType.SYNTHETIC_UTILITY_BILL
    return DocumentType.UNKNOWN


def _field(name: str, label: str, value: str | None, confidence: float, source: FieldSource) -> dict:
    return {
        "name": name,
        "label": label,
        "value": sanitize_text(value, 240) if value else None,
        "confidence": round(max(0.0, min(100.0, confidence)), 1),
        "source": source.value,
    }


def _first_key(data: dict, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalise_dob(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw[:32]


def extract_fields_from_json(payload: dict) -> tuple[list[dict], DocumentType]:
    name = _first_key(payload, JSON_NAME_KEYS)
    dob = _normalise_dob(_first_key(payload, JSON_DOB_KEYS))
    number = _first_key(payload, JSON_NUMBER_KEYS)
    address = _first_key(payload, JSON_ADDRESS_KEYS)
    type_hint = _first_key(payload, JSON_TYPE_KEYS)
    doc_type = detect_document_type(json.dumps(payload), type_hint)
    fields = [
        _field("full_name", "Full name", name, 98 if name else 20, FieldSource.RULE),
        _field("date_of_birth", "Date of birth", dob, 97 if dob else 20, FieldSource.RULE),
        _field("document_type", "Document type", doc_type_label(doc_type), 99, FieldSource.RULE),
        _field("document_number", "Document number", number, 96 if number else 15, FieldSource.RULE),
        _field("address", "Address", address, 94 if address else 25, FieldSource.RULE),
    ]
    return fields, doc_type


def extract_fields_from_text(text: str) -> tuple[list[dict], DocumentType]:
    name = _match(NAME_RE, text)
    dob = _normalise_dob(_match(DOB_RE, text))
    number = _match(NUMBER_RE, text)
    if not number:
        for pattern in (SYNTHETIC_PAN, SYNTHETIC_NATIONAL, SYNTHETIC_PASSPORT, SYNTHETIC_UTILITY):
            found = pattern.search(text)
            if found:
                number = found.group(0).upper().replace("SYNTHETIC", "SYNTHETIC")
                break
    address = _match(ADDRESS_RE, text)
    type_hint = _match(TYPE_RE, text)
    doc_type = detect_document_type(text, type_hint)
    fields = [
        _field("full_name", "Full name", name, 93 if name else 18, FieldSource.RULE),
        _field("date_of_birth", "Date of birth", dob, 92 if dob else 18, FieldSource.RULE),
        _field("document_type", "Document type", doc_type_label(doc_type), 95 if doc_type != DocumentType.UNKNOWN else 40, FieldSource.RULE),
        _field("document_number", "Document number", number, 94 if number else 16, FieldSource.RULE),
        _field("address", "Address", address, 88 if address else 22, FieldSource.RULE),
    ]
    return fields, doc_type


def _match(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def doc_type_label(doc_type: DocumentType) -> str:
    return {
        DocumentType.SYNTHETIC_PAN: "Synthetic PAN",
        DocumentType.SYNTHETIC_NATIONAL_ID: "Synthetic National ID",
        DocumentType.SYNTHETIC_PASSPORT: "Synthetic Passport",
        DocumentType.SYNTHETIC_UTILITY_BILL: "Synthetic Utility Bill",
        DocumentType.UNKNOWN: "Unknown",
    }[doc_type]


def field_value(fields: list[dict], name: str) -> str | None:
    for field in fields:
        if field.get("name") == name and field.get("value"):
            return str(field["value"])
    return None


def overall_confidence(fields: list[dict]) -> float:
    if not fields:
        return 0.0
    return round(sum(float(f.get("confidence") or 0) for f in fields) / len(fields), 1)


def mask_document_number(number: str | None) -> str | None:
    if not number:
        return None
    if len(number) <= 4:
        return "••••"
    if len(number) > 8:
        return f"{number[:4]}{'•' * (len(number) - 8)}{number[-4:]}"
    return f"••••{number[-4:]}"


def hash_document_number(number: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{number}".encode()).hexdigest()


def parse_dob(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def extract(content: bytes, filename: str, declared_type: str | None, settings: Settings) -> ExtractionResult:
    mime = validate_upload(content, filename, declared_type, settings)
    text, pages = extract_text(content, mime)

    if mime == "application/json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DocumentError("JSON document is not valid.") from exc
        if not isinstance(payload, dict):
            raise DocumentError("JSON document must be an object.")
        privacy = contains_real_identity_pattern(json.dumps(payload))
        if privacy:
            raise DocumentError(privacy)
        fields, doc_type = extract_fields_from_json(payload)
        display_text = json.dumps(payload, indent=2)
    else:
        privacy = contains_real_identity_pattern(text)
        if privacy:
            raise DocumentError(privacy)
        if mime in {"image/png", "image/jpeg"} and not text.strip():
            fields = [
                _field("full_name", "Full name", None, 20, FieldSource.OCR),
                _field("date_of_birth", "Date of birth", None, 20, FieldSource.OCR),
                _field("document_type", "Document type", "Unknown", 25, FieldSource.OCR),
                _field("document_number", "Document number", None, 15, FieldSource.OCR),
                _field("address", "Address", None, 15, FieldSource.OCR),
            ]
            doc_type = DocumentType.UNKNOWN
            display_text = (
                "No machine-readable text was found in this image. "
                "For the local demo, upload a .txt, .json or text-based PDF sample."
            )
        else:
            fields, doc_type = extract_fields_from_text(text)
            display_text = text

    return ExtractionResult(
        text=sanitize_text(display_text),
        mime_type=mime,
        page_count=pages,
        document_type=doc_type,
        fields=fields,
        sha256=hashlib.sha256(content).hexdigest(),
    )
