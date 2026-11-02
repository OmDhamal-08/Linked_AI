"""Builds structured prompts from templates. Keeps giant prompts out of route files.

Every prompt is split into a SYSTEM part and a USER part. User-supplied text is
sanitised so it cannot close our section tags or impersonate instructions.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.ai.base import AIRequest
from app.core.config import get_settings
from app.core.taxonomy import get_taxonomy

PROMPT_DIR = Path(__file__).resolve().parent
PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
FORBIDDEN_TAG_RE = re.compile(
    r"</?\s*(user_data|retrieved_intelligence|analysis|system|instructions?)\s*>",
    flags=re.IGNORECASE,
)


def sanitize_untrusted(text: str | None) -> str:
    """Neutralise section tags inside untrusted text and trim control characters."""
    if not text:
        return ""
    cleaned = FORBIDDEN_TAG_RE.sub("[tag removed]", text)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
    return cleaned.strip()


@lru_cache
def load_template(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def render(template: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        value = values.get(match.group(1), "")
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value) if value else "none"
        return str(value) if value not in (None, "") else "none"

    return PLACEHOLDER_RE.sub(replace, template)


class PromptBuilder:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._taxonomy = get_taxonomy()

    @property
    def system_prompt(self) -> str:
        return load_template("system_base.txt")

    def build_generate(
        self,
        *,
        request: Any,
        intelligence: dict[str, Any],
        blueprint: dict[str, Any],
        target_words: int,
        variant: int = 0,
        hook: str = "",
    ) -> AIRequest:
        cta_instructions = self._taxonomy["cta_instructions"]
        values = {
            "post_type": request.category,
            "topic": sanitize_untrusted(request.topic),
            "field": sanitize_untrusted(request.field),
            "event": sanitize_untrusted(request.event),
            "tone": request.tone,
            "emotion": request.emotion,
            "audience": sanitize_untrusted(request.audience),
            "length_words": target_words,
            "cta_instruction": cta_instructions.get(request.cta, cta_instructions["question"]),
            "keywords": [sanitize_untrusted(k) for k in request.keywords],
            "context": sanitize_untrusted(request.context),
            "intel_keywords": intelligence.get("recommended_keywords", []),
            "structure": blueprint["structure"],
            "hook_patterns": intelligence.get("hook_patterns", []),
            "hook": hook,
            "cta_style": request.cta,
            "hashtags": blueprint.get("hashtags", []),
            "variant": variant + 1,
        }
        user_prompt = render(load_template("generate_post.txt"), values)
        return AIRequest(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            task="generate",
            variables={
                "topic": request.topic,
                "event": request.event,
                "field": request.field,
                "tone": request.tone,
                "emotion": request.emotion,
                "audience": request.audience,
                "cta": request.cta,
                "keywords": list(request.keywords) + list(intelligence.get("recommended_keywords", [])[:3]),
                "context": request.context,
                "structure": blueprint["structure"],
                "hook": hook,
                "variant": variant,
            },
            max_tokens=self._settings.ai_max_output_tokens,
            temperature=min(1.0, self._settings.ai_temperature + 0.1 * variant),
        )

    def build_enhance(
        self,
        *,
        original_text: str,
        tone: str,
        cta: str,
        keywords: list[str],
        analysis: dict[str, Any],
        intelligence: dict[str, Any],
        hook: str,
        weaknesses: list[str],
        missing_keywords: list[str],
    ) -> AIRequest:
        cta_instructions = self._taxonomy["cta_instructions"]
        safe_original = sanitize_untrusted(original_text)
        values = {
            "original_text": safe_original,
            "tone": tone,
            "cta_instruction": cta_instructions.get(cta, cta_instructions["question"]),
            "keywords": keywords,
            "topic": analysis.get("topic", ""),
            "detected_tone": analysis.get("tone", ""),
            "weaknesses": weaknesses,
            "missing_keywords": missing_keywords,
            "structure": intelligence.get("recommended_structure", analysis.get("structure", [])),
            "hook": hook,
            "intel_keywords": intelligence.get("recommended_keywords", []),
        }
        return AIRequest(
            system_prompt=self.system_prompt,
            user_prompt=render(load_template("enhance_post.txt"), values),
            task="enhance",
            variables={
                "original_text": safe_original,
                "hook": hook,
                "cta": cta,
                "needs_cta": analysis.get("cta", "none") == "none" and cta != "none",
                "topic": analysis.get("topic", ""),
                "audience": "your field",
            },
            max_tokens=self._settings.ai_max_output_tokens,
            temperature=self._settings.ai_temperature,
        )

    def build_analyze(self, *, original_text: str, analysis: dict[str, Any]) -> AIRequest:
        values = {
            "original_text": sanitize_untrusted(original_text),
            "hook_strength": analysis.get("hook_strength"),
            "structure": analysis.get("structure", []),
            "readability": analysis.get("readability"),
            "cta": analysis.get("cta"),
        }
        return AIRequest(
            system_prompt=self.system_prompt,
            user_prompt=render(load_template("analyze_post.txt"), values),
            task="analyze",
            variables={"strengths": [], "weaknesses": []},
            max_tokens=400,
            temperature=0.2,
        )

    def build_validate(self, *, post: str, user_facts: str) -> AIRequest:
        values = {"post": sanitize_untrusted(post), "user_facts": sanitize_untrusted(user_facts)}
        return AIRequest(
            system_prompt=self.system_prompt,
            user_prompt=render(load_template("validate_post.txt"), values),
            task="validate",
            variables={},
            max_tokens=300,
            temperature=0.0,
        )

    def build_extract(self, *, text: str) -> AIRequest:
        t = self._taxonomy
        values = {
            "text": sanitize_untrusted(text),
            "categories": list(t["knowledge_categories"].keys()),
            "tones": t["tones"],
            "hook_types": list(t["hook_patterns"].keys()) + ["statement"],
            "cta_types": t["cta_types"],
        }
        return AIRequest(
            system_prompt=self.system_prompt,
            user_prompt=render(load_template("extract_intelligence.txt"), values),
            task="extract",
            variables={},
            max_tokens=500,
            temperature=0.0,
        )
