from app.config.bank_templates import BANK_KEYWORDS, DOC_TYPE_KEYWORDS


def detect_bank(first_page_text: str) -> str | None:
    t = first_page_text.lower()
    for bank, words in BANK_KEYWORDS.items():
        if any(w in t for w in words):
            return bank
    return None


def detect_doc_type(full_text: str, swift_tags: dict) -> str:
    t = full_text.lower()
    for doc_type, words in DOC_TYPE_KEYWORDS:
        if any(w in t for w in words):
            return doc_type
    # fallback on tag fingerprints: 20 + 32B + 31D is an MT700
    if {"20", "32B", "31D"} <= swift_tags.keys():
        return "MT700"
    return "UNKNOWN"