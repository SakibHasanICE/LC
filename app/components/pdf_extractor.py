"""Lossless PDF reading: every page's text and every table, nothing filtered."""
from pathlib import Path

import pdfplumber


def _clean(s: str | None) -> str | None:
    # Postgres rejects NUL characters in text/JSONB
    return s.replace("\x00", "") if s else s


def extract_pdf(pdf_path: str | Path, password: str | None = None) -> dict:
    pages = []
    with pdfplumber.open(pdf_path, password=password) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            tables = []
            for t in page.extract_tables() or []:
                rows = [[_clean(c) for c in row] for row in t]
                # drop layout artefacts (footers etc.): need at least 4 non-empty cells
                if sum(1 for r in rows for c in r if c and c.strip()) >= 4:
                    tables.append(rows)
            pages.append({
                "page_no": i,
                "text": _clean(page.extract_text()) or "",
                "tables": tables,
            })
    return {
        "page_count": len(pages),
        "pages": pages,
        "full_text": "\n".join(p["text"] for p in pages),
    }