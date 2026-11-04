REQUIRED_FOR_LC_DOCS = {"MT700": ["lc_number", "applicant", "beneficiary", "currency", "amount"],
                        "MT799": ["lc_number"],
                        "CHARGES_ADVICE": ["lc_number"]}


def review_status(doc_type: str, normalized: dict) -> tuple[str, str | None]:
    """('extracted', None) when complete, else ('needs_review', reason)."""
    if doc_type == "UNKNOWN":
        return "needs_review", "document type not recognised"
    missing = [f for f in REQUIRED_FOR_LC_DOCS.get(doc_type, []) if f not in normalized]
    if missing:
        return "needs_review", f"missing fields: {', '.join(missing)}"
    return "extracted", None