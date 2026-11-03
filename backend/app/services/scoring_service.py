"""Quality score for a post: 0-100 on eight dimensions plus a weighted overall.

These are rule-based checks on the text itself (readability, hook, keywords...).
They say nothing about how many people will see the post.
"""

from typing import Any

from app.core.taxonomy import get_taxonomy
from app.nlp.analysis import detect_cta, detect_structure, detect_tone, flesch_reading_ease, hook_score, tokenize

WEIGHTS = {
    "relevance": 0.20,
    "readability": 0.15,
    "hook_strength": 0.15,
    "structure": 0.10,
    "keyword_alignment": 0.15,
    "tone_alignment": 0.10,
    "cta_quality": 0.10,
    "originality_signals": 0.05,
}
LABEL = "Quality score (not a prediction of LinkedIn reach)"


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _originality(text: str) -> float:
    tokens = tokenize(text)
    if len(tokens) < 3:
        return 50.0
    trigrams = [tuple(tokens[i : i + 3]) for i in range(len(tokens) - 2)]
    unique_ratio = len(set(trigrams)) / len(trigrams)
    return _clamp(unique_ratio * 100)


def score_post(
    text: str,
    *,
    topic: str,
    keywords: list[str],
    tone: str,
    cta: str,
    target_structure: list[str],
    requested_keywords: list[str] | None = None,
) -> dict[str, Any]:
    lowered = text.lower()
    topic_terms = [t for t in topic.lower().split() if len(t) > 2][:4]
    relevance_terms = list(dict.fromkeys(topic_terms + [k.lower() for k in keywords[:5]]))
    relevance_hits = sum(1 for t in relevance_terms if t in lowered)
    relevance = _clamp(100 * relevance_hits / max(1, len(relevance_terms))) if relevance_terms else 70.0

    readability = flesch_reading_ease(text)
    hook = _clamp(hook_score(text) * 100)

    detected_roles = detect_structure(text)
    if target_structure:
        covered = sum(1 for role in target_structure if role in detected_roles)
        structure = _clamp(100 * covered / len(target_structure))
    else:
        structure = 70.0

    requested = requested_keywords if requested_keywords is not None else keywords
    if requested:
        used = sum(1 for k in requested if k.lower() in lowered)
        keyword_alignment = _clamp(100 * used / len(requested))
    else:
        keyword_alignment = 70.0

    detected_tone = detect_tone(text)
    if detected_tone == tone:
        tone_alignment = 95.0
    elif tone in _tone_neighbours(detected_tone):
        tone_alignment = 75.0
    else:
        tone_alignment = 50.0

    detected_cta = detect_cta(text)
    if cta == "none":
        cta_quality = 85.0 if detected_cta == "none" else 65.0
    elif detected_cta == cta:
        cta_quality = 95.0
    elif detected_cta != "none":
        cta_quality = 70.0
    else:
        cta_quality = 30.0

    originality = _originality(text)

    dimensions = {
        "relevance": relevance,
        "readability": _clamp(readability),
        "hook_strength": hook,
        "structure": structure,
        "keyword_alignment": keyword_alignment,
        "tone_alignment": tone_alignment,
        "cta_quality": cta_quality,
        "originality_signals": originality,
    }
    overall = sum(dimensions[k] * WEIGHTS[k] for k in WEIGHTS)
    return {"label": LABEL, **{k: round(v) for k, v in dimensions.items()}, "overall": round(overall)}


def _tone_neighbours(tone: str) -> set[str]:
    neighbours = {
        "proud": {"excited", "confident", "grateful"},
        "excited": {"proud", "motivational"},
        "humble": {"grateful", "reflective"},
        "reflective": {"humble", "educational"},
        "motivational": {"excited", "confident"},
        "grateful": {"humble", "proud"},
        "educational": {"professional", "reflective"},
        "conversational": {"humble", "educational"},
        "confident": {"proud", "professional"},
        "professional": {"educational", "confident"},
    }
    return neighbours.get(tone, set())


def taxonomy_structure_for(post_type: str, length: str) -> list[str]:
    hints = get_taxonomy()["category_to_structure_hint"]
    if post_type in hints:
        return list(hints[post_type])
    return list(get_taxonomy()["structures"].get(length, get_taxonomy()["structures"]["medium"]))
