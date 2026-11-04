"""PDF -> read everything -> detect bank/type -> parse -> normalise -> Postgres."""
from pathlib import Path

from app.common.logger import get_logger
from app.components.db_writer import save_document
from app.components.field_parser import parse_key_values, parse_swift_tags
from app.components.format_detector import detect_bank, detect_doc_type
from app.components.pdf_extractor import extract_pdf
from app.components.template_matcher import normalize
from app.components.validator import review_status
from app.db.session import SessionLocal, init_db

logger = get_logger(__name__)


def process_pdf(pdf_path: Path, email_meta: dict | None = None) -> None:
    init_db()
    kwargs: dict = {}
    try:
        pdf = extract_pdf(pdf_path)
        text = pdf["full_text"]
        swift = parse_swift_tags(text)
        key_values = parse_key_values(text)
        doc_type = detect_doc_type(text, swift)
        normalized = normalize(swift, key_values)
        status, reason = review_status(doc_type, normalized)
        kwargs = dict(
            doc_type=doc_type,
            bank=detect_bank(pdf["pages"][0]["text"] if pdf["pages"] else ""),
            extracted={"swift": swift, "key_values": key_values},
            normalized=normalized,
            raw_text=text,
            pages=pdf["pages"],
            status=status,
            error=reason,
        )
    except Exception as e:  # unreadable / password-protected PDF: still store the file record
        logger.exception(f"Extraction failed for {pdf_path.name}")
        kwargs = dict(doc_type="UNKNOWN", bank=None, status="failed", error=str(e), method="none")

    with SessionLocal() as db:
        doc = save_document(db, file_path=str(pdf_path), email_meta=email_meta, **kwargs)
        logger.info(
            f"Stored document id={doc.id} type={doc.doc_type} bank={doc.bank} "
            f"status={doc.status} lc={doc.normalized.get('lc_number')}"
        )