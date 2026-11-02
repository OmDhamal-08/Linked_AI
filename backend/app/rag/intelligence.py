"""Aggregates retrieved records into content intelligence (patterns only, no source text)."""

from collections import Counter
from typing import Any

from app.core.taxonomy import get_taxonomy
from app.nlp.analysis import to_camel_concept
from app.rag.query_builder import AnalyzedQuery

DEFAULT_STRUCTURES = {
    "short": ["hook", "achievement", "learning", "cta"],
    "medium": ["hook", "context", "achievement", "learning", "cta"],
    "long": ["hook", "context", "problem", "solution", "result", "learning", "cta"],
}


def build_content_intelligence(items: list[dict[str, Any]], query: AnalyzedQuery) -> dict[str, Any]:
    taxonomy = get_taxonomy()
    keyword_weights: Counter[str] = Counter()
    hook_weights: Counter[str] = Counter()
    structure_weights: Counter[tuple[str, ...]] = Counter()
    cta_weights: Counter[str] = Counter()
    hashtag_weights: Counter[str] = Counter()

    for item in items:
        weight = max(0.01, float(item.get("score", 0.0)))
        for kw in item.get("keywords", []):
            keyword_weights[kw] += weight
        hook_weights[item.get("hook_pattern") or item.get("hook_type", "statement")] += weight
        if item.get("structure"):
            structure_weights[tuple(item["structure"])] += weight
        if item.get("cta_type") and item["cta_type"] != "none":
            cta_weights[item["cta_type"]] += weight
        for tag in item.get("hashtag_concepts", []):
            hashtag_weights[tag] += weight

    recommended_keywords = [k for k, _ in keyword_weights.most_common(6)]
    for kw in query.keywords:
        if kw not in recommended_keywords:
            recommended_keywords.append(kw)

    if structure_weights:
        structure = list(structure_weights.most_common(1)[0][0])
    else:
        structure = DEFAULT_STRUCTURES.get(query.length, DEFAULT_STRUCTURES["medium"])
    if query.cta_type != "none":
        cta_style = query.cta_type
    elif cta_weights:
        cta_style = cta_weights.most_common(1)[0][0]
    else:
        cta_style = "question"

    hashtags = [t for t, _ in hashtag_weights.most_common(5)]
    if not hashtags:
        hashtags = [to_camel_concept(k) for k in recommended_keywords[:3] if len(k) > 2]

    return {
        "recommended_keywords": recommended_keywords[:8],
        "hook_patterns": [h for h, _ in hook_weights.most_common(3)],
        "recommended_structure": structure,
        "recommended_cta": cta_style,
        "hashtag_concepts": hashtags[:5],
        "source_count": len(items),
        "cta_instructions": taxonomy["cta_instructions"].get(cta_style, ""),
    }
