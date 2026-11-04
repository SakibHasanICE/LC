"""Detection keywords. Add a bank / document type here - no other code changes needed."""

# matched case-insensitively against the first page's text
BANK_KEYWORDS = {
    "HSBC": ["hsbc", "hongkong and shanghai banking"],
    "BRAC": ["brac bank"],
    "SCB":  ["standard chartered"],
    "EBL":  ["eastern bank"],
}

# checked in order; first match wins. Matched case-insensitively against the full text
DOC_TYPE_KEYWORDS = [
    ("PACS008",        ["pacs.008", "fitoficustomercredittransfer"]),
    ("MT700",          ["swift700", "mt700", "issue of a documentary credit"]),
    ("MT799",          ["swift799", "mt799", "free format message"]),
    ("CHARGES_ADVICE", ["charges advice"]),
]