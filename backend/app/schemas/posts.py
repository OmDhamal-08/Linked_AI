import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import get_settings
from app.core.taxonomy import get_taxonomy

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean(value: str) -> str:
    return CONTROL_CHARS.sub("", value).strip()


def _check_choice(value: str, allowed: list[str], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"{label} must be one of: {', '.join(allowed)}")
    return value


class GenerateRequest(BaseModel):
    """Structured input for generating a new post."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(description="Post type, e.g. achievement, project, certification")
    topic: str = Field(min_length=2, max_length=120)
    event: str = Field(min_length=5, max_length=500, description="Achievement or event in one sentence")
    field: str = Field(default="", max_length=120)
    tone: str = "professional"
    emotion: str = "neutral"
    audience: str = Field(default="students and professionals", max_length=120)
    length: str = "medium"
    cta: str = "question"
    keywords: list[str] = Field(default_factory=list, max_length=10)
    context: str = Field(default="", max_length=get_settings().max_input_chars)
    variations: int = Field(default=1, ge=1, le=3)

    @field_validator("category")
    @classmethod
    def _category(cls, v: str) -> str:
        return _check_choice(v, get_taxonomy()["post_types"], "category")

    @field_validator("tone")
    @classmethod
    def _tone(cls, v: str) -> str:
        return _check_choice(v, get_taxonomy()["tones"], "tone")

    @field_validator("emotion")
    @classmethod
    def _emotion(cls, v: str) -> str:
        return _check_choice(v, get_taxonomy()["emotions"], "emotion")

    @field_validator("length")
    @classmethod
    def _length(cls, v: str) -> str:
        return _check_choice(v, get_taxonomy()["length_options"], "length")

    @field_validator("cta")
    @classmethod
    def _cta(cls, v: str) -> str:
        return _check_choice(v, get_taxonomy()["cta_types"], "cta")

    @field_validator("topic", "event", "field", "audience", "context")
    @classmethod
    def _strip(cls, v: str) -> str:
        return _clean(v)

    @field_validator("keywords")
    @classmethod
    def _keywords(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        for kw in v:
            kw = _clean(kw)[:40]
            if kw and kw.lower() not in {c.lower() for c in cleaned}:
                cleaned.append(kw)
        return cleaned


class EnhanceRequest(BaseModel):
    """Input for enhancing an existing post."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=30, max_length=get_settings().max_input_chars)
    tone: str | None = None
    cta: str = "question"
    keywords: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("text")
    @classmethod
    def _text(cls, v: str) -> str:
        return _clean(v)

    @field_validator("tone")
    @classmethod
    def _tone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _check_choice(v, get_taxonomy()["tones"], "tone")

    @field_validator("cta")
    @classmethod
    def _cta(cls, v: str) -> str:
        return _check_choice(v, get_taxonomy()["cta_types"], "cta")


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=30, max_length=get_settings().max_input_chars)
    advanced: bool = False

    @field_validator("text")
    @classmethod
    def _text(cls, v: str) -> str:
        return _clean(v)


class PostUpdate(BaseModel):
    output_text: str | None = Field(default=None, max_length=get_settings().max_input_chars)
    hashtags: list[str] | None = Field(default=None, max_length=10)
    title: str | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> "PostUpdate":
        if self.output_text is None and self.hashtags is None:
            raise ValueError("Provide output_text or hashtags to update.")
        return self

    @field_validator("hashtags")
    @classmethod
    def _tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned = []
        for tag in v:
            tag = re.sub(r"[^A-Za-z0-9_]", "", tag.lstrip("#"))[:40]
            if tag and tag not in cleaned:
                cleaned.append(tag)
        return cleaned


PostPayload = dict[str, Any]
