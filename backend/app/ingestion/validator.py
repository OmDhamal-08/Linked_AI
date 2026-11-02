"""Row validation for dataset ingestion.

Checks that a raw row has usable text and normalises the optional metadata.
Values that are not in the taxonomy are dropped (set to None) so the NLP
pipeline regenerates them instead of storing junk labels.
"""

import re
from typing import Any

from app.core.taxonomy import get_taxonomy
from app.ingestion.cleaner import clean_text

MIN_TEXT_CHARS = 40
MAX_TEXT_CHARS = 5000
LIST_SPLIT_RE = re.compile(r"[;,|\n]")


def parse_list(value: Any) -> list[str]:
    """Turn 'a;b|c, d' or ['#a', 'b'] into a clean list, deduplicated case-insensitively."""
    if value is None:
        return []
    if isinstance(value, str):
        parts = LIST_SPLIT_RE.split(value)
    elif isinstance(value, (list, tuple)):
        parts = [str(v) for v in value if v is not None]
    else:
        parts = [str(value)]

    seen: set[str] = set()
    items: list[str] = []
    for part in parts:
        item = part.strip().lstrip("#").strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            items.append(item)
    return items


def _text_or_none(value: Any, limit: int = 200) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:limit] or None


def _pick(value: Any, allowed: list[str]) -> str | None:
    """Case-insensitive match against a taxonomy list; returns the canonical value."""
    text = _text_or_none(value)
    if not text:
        return None
    lookup = {option.lower(): option for option in allowed}
    return lookup.get(text.lower())


def validate_record(row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Return (record, None) for a usable row, or (None, reason) when it must be rejected."""
    raw_text = row.get("text")
    if raw_text is None or not str(raw_text).strip():
        return None, "missing_text"

    text = clean_text(str(raw_text))
    if len(text) < MIN_TEXT_CHARS:
        return None, "text_too_short"
    if len(text) > MAX_TEXT_CHARS:
        return None, "text_too_long"

    taxonomy = get_taxonomy()
    hook_types = list(taxonomy["hook_patterns"].keys()) + ["statement"]
    roles = set(taxonomy["structure_roles"].keys()) | {"hook", "cta"}
    structure = [s.lower() for s in parse_list(row.get("structure")) if s.lower() in roles]

    record = {
        "text": text,
        "category": _pick(row.get("category"), list(taxonomy["knowledge_categories"].keys())),
        "topic": _text_or_none(row.get("topic")),
        "keywords": [k.lower() for k in parse_list(row.get("keywords"))],
        "tone": _pick(row.get("tone"), taxonomy["tones"]),
        "hook_type": _pick(row.get("hook_type"), hook_types),
        "structure": structure or None,
        "cta_type": _pick(row.get("cta_type"), taxonomy["cta_types"]),
        "hashtags": parse_list(row.get("hashtags")),
        "audience": _pick(row.get("audience"), taxonomy["audiences"]),
    }
    return record, None
