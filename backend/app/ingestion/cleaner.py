"""Text cleaning and content hashing used for deduplication."""

import hashlib
import html
import re
import unicodedata

TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
ZERO_WIDTH_RE = re.compile(r"[​-‍﻿]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_text(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw)
    text = html.unescape(text)
    text = TAG_RE.sub(" ", text)
    text = URL_RE.sub("", text)
    text = ZERO_WIDTH_RE.sub("", text)
    text = CONTROL_RE.sub("", text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def content_hash(text: str) -> str:
    """Hash of the normalised text. Used only for dedupe; the text itself is not stored."""
    normalised = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()
