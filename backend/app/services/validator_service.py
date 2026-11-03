"""Post Validator: checks AI output before it reaches the user.

Severe issues trigger one regeneration in PostService. Minor issues are cleaned
or reported as suggestions.
"""

import re
from dataclasses import dataclass, field

from app.core.config import Settings
from app.core.taxonomy import get_taxonomy
from app.nlp.analysis import tokenize, word_count

PREAMBLE_RE = re.compile(r"^\s*(here('?s| is)|sure[,!]|certainly[,!]|of course[,!]).*:\s*$", re.IGNORECASE)
NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?%?")


@dataclass
class ValidationIssue:
    severity: str  # severe | warning
    code: str
    message: str


@dataclass
class ValidationResult:
    cleaned_text: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_severe(self) -> bool:
        return any(i.severity == "severe" for i in self.issues)

    @property
    def codes(self) -> list[str]:
        return [i.code for i in self.issues]


class PostValidator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._taxonomy = get_taxonomy()

    def validate(
        self,
        text: str,
        *,
        user_facts: str,
        target_words: int,
        keywords: list[str],
        topic: str,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []
        cleaned = self._clean(text)

        if not cleaned:
            issues.append(ValidationIssue("severe", "empty_output", "The model returned no usable text."))
            return ValidationResult(cleaned, issues)

        lowered = cleaned.lower()
        leakage = [t for t in self._taxonomy["leakage_terms"] if re.search(r"\b" + re.escape(t) + r"\b", lowered)]
        if leakage:
            issues.append(ValidationIssue("severe", "leakage", "Output mentions internal system terms."))

        spam = [p for p in self._taxonomy["spam_phrases"] if p in lowered]
        if spam:
            issues.append(ValidationIssue("severe", "spam_language", "Output contains spam-like or guaranteed-result language."))

        if "#" in cleaned:
            tags = re.findall(r"#\w+", cleaned)
            if len(tags) > self._settings.hashtag_max:
                issues.append(ValidationIssue("warning", "excessive_hashtags", "Too many hashtags in the body."))
                cleaned = re.sub(r"#\w+", "", cleaned)
                cleaned = re.sub(r"[ \t]+\n", "\n", cleaned).strip()

        words = word_count(cleaned)
        low, high = int(target_words * 0.6), int(target_words * 1.5)
        if words > high:
            issues.append(ValidationIssue("warning", "too_long", f"Output is {words} words; target is about {target_words}."))
        elif words < low:
            issues.append(ValidationIssue("warning", "too_short", f"Output is {words} words; target is about {target_words}."))

        if topic and not any(t in lowered for t in tokenize(topic)[:3]):
            issues.append(ValidationIssue("warning", "topic_drift", "Output may not reference the requested topic."))

        if keywords:
            hits = sum(1 for k in keywords if k.lower() in lowered)
            if hits == 0:
                issues.append(ValidationIssue("warning", "keyword_relevance", "None of the requested keywords appear."))

        paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        if len(paragraphs) != len(set(paragraphs)):
            issues.append(ValidationIssue("severe", "repetition", "Output repeats a paragraph."))

        facts = user_facts.lower()
        invented = [n for n in NUMBER_RE.findall(cleaned) if n not in facts and n.rstrip("%") not in facts]
        if invented:
            issues.append(ValidationIssue("warning", "unsupported_number", "Check numbers that were not in your input."))

        return ValidationResult(cleaned, issues)

    @staticmethod
    def _clean(text: str) -> str:
        lines = [ln.rstrip() for ln in (text or "").strip().splitlines()]
        if lines and PREAMBLE_RE.match(lines[0]):
            lines = lines[1:]
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip().strip('"').strip()
