"""Query Analyzer: turns structured user input (or an existing post) into a semantic RAG query."""

from dataclasses import dataclass, field

from app.nlp.analysis import detect_category, extract_keywords


@dataclass
class AnalyzedQuery:
    semantic_query: str
    knowledge_category: str | None
    keywords: list[str]
    tone: str
    emotion: str = "neutral"
    audience: str = ""
    post_type: str = ""
    length: str = "medium"
    cta_type: str = "none"
    topic: str = ""
    category_scores: dict[str, int] = field(default_factory=dict)

    @property
    def metadata_filters(self) -> dict[str, str | None]:
        return {"category": self.knowledge_category}


class QueryAnalyzer:
    def for_generation(self, request) -> AnalyzedQuery:
        combined = " ".join(
            filter(None, [request.topic, request.field, request.event, " ".join(request.keywords), request.context])
        )
        category, scores = detect_category(combined)
        keywords = list(dict.fromkeys([k.lower() for k in request.keywords] + extract_keywords(combined, limit=6)))
        parts = [
            category or "",
            request.topic,
            request.field,
            request.category.replace("_", " "),
            " ".join(keywords[:6]),
            request.tone,
            request.emotion,
            request.length,
            "LinkedIn post",
        ]
        return AnalyzedQuery(
            semantic_query=" ".join(p for p in parts if p),
            knowledge_category=category,
            keywords=keywords,
            tone=request.tone,
            emotion=request.emotion,
            audience=request.audience,
            post_type=request.category,
            length=request.length,
            cta_type=request.cta,
            topic=request.topic,
            category_scores=scores,
        )

    def for_text(self, text: str, *, analysis: dict, tone_hint: str | None = None) -> AnalyzedQuery:
        category, scores = detect_category(text)
        keywords = analysis.get("keywords", [])[:6]
        parts = [category or "", analysis.get("topic", ""), " ".join(keywords), analysis.get("post_type", "").replace("_", " "), tone_hint or analysis.get("tone", ""), "LinkedIn post"]
        return AnalyzedQuery(
            semantic_query=" ".join(p for p in parts if p),
            knowledge_category=category,
            keywords=keywords,
            tone=tone_hint or analysis.get("tone", "professional"),
            emotion=analysis.get("emotion", "neutral"),
            post_type=analysis.get("post_type", ""),
            topic=analysis.get("topic", ""),
            category_scores=scores,
        )
