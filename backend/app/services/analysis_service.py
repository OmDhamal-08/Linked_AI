"""Content analysis and suggestion building (deterministic, no LLM cost)."""

import re
from typing import Any

from app.core.taxonomy import get_taxonomy
from app.nlp.analysis import analyze_text, first_line, tokenize

GENERIC_OPENER_RE = re.compile(r"^(" + "|".join(re.escape(o) for o in get_taxonomy()["generic_openers"]) + ")", re.I)


def analyze_post(text: str) -> dict[str, Any]:
    return analyze_text(text)


def missing_elements(analysis: dict[str, Any], text: str, intelligence_keywords: list[str]) -> list[str]:
    missing: list[str] = []
    if analysis["hook_strength"] < 0.6:
        missing.append("weak_hook")
    if GENERIC_OPENER_RE.match(first_line(text)):
        missing.append("generic_opener")
    if analysis["cta"] == "none":
        missing.append("missing_cta")
    lowered = text.lower()
    absent = [k for k in intelligence_keywords if k.lower() not in lowered]
    if absent:
        missing.append("missing_keywords")
    if analysis["length_words"] > 320:
        missing.append("too_long")
    if analysis["length_words"] < 40:
        missing.append("too_short")
    if analysis["readability"] < 45:
        missing.append("low_readability")
    if len(analysis["hashtags"]) > 5:
        missing.append("excess_hashtags")
    if len(analysis["structure"]) < 3:
        missing.append("no_structure")
    if not re.search(r"\d", text) and len(tokenize(text)) > 40:
        missing.append("no_specifics")
    return missing


def build_suggestions(missing: list[str], *, missing_keywords: list[str]) -> list[dict[str, str]]:
    messages = get_taxonomy()["suggestion_messages"]
    suggestions: list[dict[str, str]] = []
    for code in missing:
        text = messages.get(code, "")
        if code == "missing_keywords":
            text = text.format(keywords=", ".join(missing_keywords[:4]) or "your key terms")
        if text:
            suggestions.append({"code": code, "message": text})
    return suggestions


def build_hook_suggestions(topic: str, event: str, hook_types: list[str]) -> list[str]:
    templates = get_taxonomy()["hook_templates"]
    event = GENERIC_OPENER_RE.sub("", event.strip()).lstrip(" :,-")
    event = re.sub(r"^that\s+", "", event, flags=re.IGNORECASE)
    event_clean = event.strip().rstrip(".!?")
    event_lower = event_clean[:1].lower() + event_clean[1:] if event_clean else event_clean
    results: list[str] = []
    for hook_type in hook_types + ["achievement", "question", "lesson"]:
        for template in templates.get(hook_type, [])[:1]:
            line = template.format(topic=topic or "this topic", event=event_clean or topic, event_lower=event_lower or topic)
            if line not in results:
                results.append(line)
        if len(results) >= 3:
            break
    return results[:3]
