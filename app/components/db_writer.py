import hashlib
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.logger import get_logger
from app.db.models import Document, DocumentPage, LetterOfCredit

logger = get_logger(__name__)

# canonical keys that live in the letters_of_credit table
LC_FIELDS = (
    "applicant", "beneficiary", "currency", "amount",
    "issue_date", "expiry_date", "latest_shipment_date",
)


def sha256_of(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_safe(obj):
    """dates / Decimals -> strings so the dict can go into a JSONB column."""
    return json.loads(json.dumps(obj, default=str))


def save_document(
    db: Session,
    *,
    file_path: str,
    doc_type: str,
    bank: str | None,
    extracted: dict | None = None,
    normalized: dict | None = None,
    raw_text: str | None = None,
    pages: list[dict] | None = None,
    email_meta: dict | None = None,
    method: str = "rules",
    confidence: float | None = None,
    status: str = "extracted",
    error: str | None = None,
) -> Document:
    """Idempotent: the same PDF (by hash) is never stored twice."""
    file_hash = sha256_of(file_path)
    existing = db.scalar(select(Document).where(Document.file_hash == file_hash))
    if existing:
        logger.info("Duplicate document skipped: %s", file_path)
        return existing

    normalized = normalized or {}
    lc = None
    lc_number = normalized.get("lc_number")
    if lc_number:
        lc = db.scalar(select(LetterOfCredit).where(LetterOfCredit.lc_number == lc_number))
        if lc is None:
            lc = LetterOfCredit(lc_number=lc_number, bank=bank)
            db.add(lc)
        # fill blanks only; a later MT799 never overwrites MT700 master data
        for key in LC_FIELDS:
            if normalized.get(key) is not None and getattr(lc, key) is None:
                setattr(lc, key, normalized[key])
        db.flush()

    meta = email_meta or {}
    doc = Document(
        lc_id=lc.id if lc else None,
        doc_type=doc_type,
        bank=bank,
        email_uid=meta.get("uid"),
        email_sender=meta.get("sender"),
        email_subject=meta.get("subject"),
        received_at=meta.get("date"),
        file_name=Path(file_path).name,
        file_path=str(file_path),
        file_hash=file_hash,
        page_count=len(pages) if pages else None,
        raw_text=raw_text,
        extracted=_json_safe(extracted or {}),
        normalized=_json_safe(normalized),
        extraction_method=method,
        confidence=confidence,
        status=status,
        error=error,
    )
    for p in pages or []:
        doc.pages.append(DocumentPage(page_no=p["page_no"], text=p["text"], tables=p["tables"]))
    db.add(doc)
    db.commit()
    return doc