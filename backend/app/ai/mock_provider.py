"""Deterministic mock LLM for development, tests and UI work without API credits.

It composes text ONLY from the user's own inputs and the structured variables
supplied by the PromptBuilder, so it never fabricates achievements or statistics.
"""

import hashlib
import json
import time

from app.ai.base import AIProvider, AIRequest, AIResult, estimate_tokens

TONE_REFLECTIONS = {
    "proud": "I'm proud of the progress, and grateful for every step that got here.",
    "grateful": "I'm grateful for the people and resources that made this possible.",
    "humble": "I'm still learning, and this experience reminded me how much there is left to explore.",
    "excited": "I'm genuinely excited about what comes next.",
    "reflective": "Looking back, the process mattered as much as the outcome.",
    "motivational": "Keep going, even when progress feels slow. Consistency compounds.",
    "educational": "Here is the practical takeaway for anyone exploring this area.",
    "confident": "I'm confident in the approach and ready for the next challenge.",
    "professional": "The work reinforced the importance of clear goals and steady execution.",
    "conversational": "Honestly, this one taught me more than I expected.",
}

CTA_LINES = {
    "question": "What part of {topic} would you like to explore next?",
    "invite_comments": "Share your own experience with {topic} in the comments.",
    "share": "If this could help someone in {audience}, feel free to share it.",
    "follow": "Follow along for more on {topic}.",
    "none": "",
}

GENERIC_OPENERS = ("excited to share", "happy to share", "pleased to announce", "thrilled to announce")


def _variant_index(seed: str, options: int) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % max(1, options)


def _sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    return text if text[-1] in ".!?" else text + "."


class MockAIProvider(AIProvider):
    name = "mock"

    def __init__(self, model: str = "mock-linkdine-v1") -> None:
        self.model = model

    def complete(self, request: AIRequest) -> AIResult:
        started = time.perf_counter()
        handler = {
            "generate": self._generate,
            "enhance": self._enhance,
            "analyze": self._analyze,
            "extract": self._extract,
            "validate": self._validate,
        }.get(request.task, self._generate)
        text = handler(request.variables)
        latency = (time.perf_counter() - started) * 1000
        return AIResult(
            text=text,
            provider=self.name,
            model=self.model,
            input_tokens=estimate_tokens(request.system_prompt + request.user_prompt),
            output_tokens=estimate_tokens(text),
            latency_ms=round(latency, 2),
        )

    # ---- task handlers -------------------------------------------------

    def _generate(self, v: dict) -> str:
        topic = v.get("topic", "this topic")
        event = _sentence(v.get("event", ""))
        keywords = [k for k in v.get("keywords", []) if k][:4]
        tone = v.get("tone", "professional")
        cta = v.get("cta", "question")
        structure = v.get("structure") or ["hook", "context", "achievement", "learning", "cta"]
        seed = f"{event}|{topic}|{tone}|{v.get('variant', 0)}"

        blocks: list[str] = []
        for role in structure:
            if role == "hook":
                blocks.append(v.get("hook") or event)
            elif role == "context":
                context_bits = [f"This came from my work on {topic}"]
                if v.get("field"):
                    context_bits.append(f"in {v['field']}")
                line = " ".join(context_bits) + "."
                if v.get("context"):
                    line += " " + _sentence(v["context"])
                blocks.append(line)
            elif role in ("achievement", "problem", "solution", "result"):
                if role == "achievement" and event:
                    blocks.append(f"The result I'm most pleased with is the working version of {topic}.")
                elif role == "problem":
                    blocks.append(f"The main challenge was getting {topic} to work the way I intended.")
                elif role == "solution":
                    blocks.append("I broke the work into small steps and reviewed each one.")
                elif role == "result" and event:
                    blocks.append(f"Where things stand now: {event}")
            elif role == "learning":
                if keywords:
                    blocks.append("Key ideas that shaped this work: " + ", ".join(keywords) + ".")
                blocks.append(
                    TONE_REFLECTIONS.get(tone, TONE_REFLECTIONS["professional"])
                    if _variant_index(seed, 2) == 0
                    else "Practical lessons matter more than perfect plans."
                )
            elif role == "reflection":
                blocks.append(TONE_REFLECTIONS.get(tone, TONE_REFLECTIONS["professional"]))
            elif role == "cta":
                line = CTA_LINES.get(cta, CTA_LINES["question"]).format(
                    topic=topic, audience=v.get("audience", "your field")
                )
                if line:
                    blocks.append(line)

        body = "\n\n".join(b.strip() for b in blocks if b and b.strip())
        return body

    def _enhance(self, v: dict) -> str:
        original = (v.get("original_text") or "").strip()
        hook = (v.get("hook") or "").strip()
        lines = original.splitlines()
        if lines and lines[0].lower().startswith(GENERIC_OPENERS):
            lines = lines[1:]
        rest = "\n".join(lines).strip()
        parts: list[str] = []
        if hook:
            parts.append(hook)
        if rest:
            parts.append(rest)
        cta = v.get("cta", "question")
        if v.get("needs_cta") and CTA_LINES.get(cta):
            parts.append(CTA_LINES[cta].format(topic=v.get("topic", "this topic"), audience=v.get("audience", "your field")))
        return "\n\n".join(parts)

    def _analyze(self, v: dict) -> str:
        return json.dumps(
            {
                "strengths": v.get("strengths", []),
                "weaknesses": v.get("weaknesses", []),
                "priority_fix": (v.get("weaknesses") or ["Keep the current structure."])[0],
            }
        )

    def _extract(self, v: dict) -> str:
        return json.dumps({"keywords": v.get("keywords", []), "tone": v.get("tone", "professional")})

    def _validate(self, v: dict) -> str:
        return json.dumps({"valid": True, "issues": []})
