"""PII detection and redaction for ingested text. Runs before any embedding or storage."""

import re

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    # Order matters: specific identifiers are matched before the broader phone pattern.
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "AADHAAR": re.compile(r"(?<!\d)\d{4}\s\d{4}\s\d{4}(?!\d)"),
    "PAN": re.compile(r"(?<![A-Za-z])[A-Z]{5}\d{4}[A-Z](?![A-Za-z])"),
    "PHONE": re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)\d{3,4}[\s-]?\d{3,4}(?!\w)"),
}


def detect_and_redact(text: str) -> tuple[str, list[str]]:
    found: list[str] = []
    redacted = text
    for label, pattern in PII_PATTERNS.items():
        if pattern.search(redacted):
            found.append(label)
            redacted = pattern.sub(f"[REDACTED_{label}]", redacted)
    return redacted, found
