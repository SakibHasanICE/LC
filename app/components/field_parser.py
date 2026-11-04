"""
Bank-independent parsing. Every pass keeps ALL the data it finds:

1. SWIFT tags - ':20 : TITLE' + ': : value' rows (HSBC style) or ':20:value' (plain
   SWIFT). Tags are an international standard, so this works for every bank's MT700/MT799.
2. Key/values - 'Our Reference No.: DPCBD1161985' style label lines (cover letters).
Tables are captured separately by pdf_extractor.
"""
import re

_TAG_LINE = re.compile(r"^:(\d{2}[A-Z]?|TO|FROM)\s*:\s*(.*)$")
_CONT_LINE = re.compile(r"^:\s*:\s?(.*)$")
_KV_LINE = re.compile(r"^([A-Za-z][A-Za-z0-9 /().'&-]{2,60}?)\s*:\s+(\S.*)$")


def parse_swift_tags(text: str) -> dict[str, dict]:
    """{'20': {'title': 'DOCUMENTARY CREDIT NUMBER', 'value': 'DPCBD1161985'}, ...}
    A repeated tag keeps every occurrence (value joined by a blank line)."""
    blocks: list[dict] = []
    current = None
    # plain SWIFT (':59:/1234' then bare lines) vs HSBC style (': : value' rows)
    colon_rows = any(_CONT_LINE.match(l.rstrip()) for l in text.splitlines())
    for raw in text.splitlines():
        line = raw.rstrip()
        if not colon_rows and current is not None and line and not _TAG_LINE.match(line):
            current["lines"].append(line.strip())       # bare continuation line
            continue
        if _CONT_LINE.match(line):                      # ': : value'
            if current is not None:
                val = _CONT_LINE.match(line).group(1).strip()
                if val:
                    current["lines"].append(val)
            continue
        m = _TAG_LINE.match(line)
        if m:                                           # ':20 : TITLE' or ':20:value'
            current = {"tag": m.group(1), "head": m.group(2).strip(), "lines": []}
            blocks.append(current)

    fields: dict[str, dict] = {}
    for b in blocks:
        if b["lines"] and colon_rows:                   # head is the field title
            title, value = b["head"] or None, "\n".join(b["lines"])
        elif b["lines"]:                                # plain SWIFT: head is 1st value line
            title, value = None, "\n".join([b["head"], *b["lines"]]).strip()
        else:                                           # head is the value itself
            title, value = None, b["head"]
        if b["tag"] in fields:
            fields[b["tag"]]["value"] += "\n\n" + value
        else:
            fields[b["tag"]] = {"title": title, "value": value}
    return fields


def parse_key_values(text: str) -> dict[str, str]:
    """'Label: value' lines. Duplicate labels get '#2', '#3'... nothing is dropped."""
    kv: dict[str, str] = {}
    for line in text.splitlines():
        if line.lstrip().startswith(":"):               # SWIFT rows handled above
            continue
        m = _KV_LINE.match(line.strip())
        if not m:
            continue
        key, val = m.group(1).strip(), m.group(2).strip()
        if val.endswith(":"):                           # side-by-side layout artefact
            continue
        base, n = key, 2
        while key in kv:
            key, n = f"{base} #{n}", n + 1
        kv[key] = val
    return kv
