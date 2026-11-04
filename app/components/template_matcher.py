"""Maps parsed fields to the canonical LC fields (the columns of letters_of_credit)."""
import re
from datetime import date
from decimal import Decimal, InvalidOperation


def _yymmdd(s: str | None) -> date | None:
    m = re.match(r"^(\d{2})(\d{2})(\d{2})", s or "")
    if not m:
        return None
    yy, mm, dd = map(int, m.groups())
    try:
        return date(2000 + yy, mm, dd)
    except ValueError:
        return None


def _first_line(value: str | None) -> str | None:
    for line in (value or "").splitlines():
        line = line.strip()
        if line and not line.startswith("/"):   # skip SWIFT account lines like '/1234'
            return line
    return None


def _amount(s: str) -> Decimal | None:
    s = s.replace(" ", "")
    s = s.replace(".", "").replace(",", ".") if "," in s else s.replace(",", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def normalize(swift: dict, key_values: dict) -> dict:
    """Canonical fields from SWIFT tags first, cover-letter labels as fallback."""
    v = lambda tag: (swift.get(tag) or {}).get("value")
    out: dict = {}

    out["lc_number"] = _first_line(v("20")) or key_values.get("Our Reference No.")
    out["issue_date"] = _yymmdd(v("31C"))
    out["expiry_date"] = _yymmdd(v("31D"))
    if v("31D") and len(v("31D")) > 6:
        out["expiry_place"] = v("31D")[6:].strip()
    out["latest_shipment_date"] = _yymmdd(v("44C"))
    out["applicant"] = _first_line(v("50"))
    out["beneficiary"] = _first_line(v("59"))

    m = re.match(r"^\s*([A-Z]{3})\s*([\d.,\s]+)", v("32B") or "")
    if m:
        out["currency"], out["amount"] = m.group(1), _amount(m.group(2))
    elif key_values.get("Documentary Credit Amount"):
        m = re.match(r"([A-Z]{3})\s*([\d.,]+)", key_values["Documentary Credit Amount"])
        if m:
            out["currency"], out["amount"] = m.group(1), _amount(m.group(2))

    return {k: val for k, val in out.items() if val is not None}