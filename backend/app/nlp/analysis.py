"""Deterministic text analysis shared by ingestion and the post analyzer.

These are rule-based NLP helpers (no LLM calls), so they are free, fast and
testable. Lexicons and regex patterns live in core/taxonomy.json.
"""

import re
from collections import Counter
from typing import Any

from app.core.taxonomy import get_taxonomy

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.]*[a-zA-Z0-9+#]|[a-zA-Z]")
HASHTAG_RE = re.compile(r"#([A-Za-z][A-Za-z0-9_]{1,40})")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")
VOWEL_GROUP_RE = re.compile(r"[aeiouy]+", re.IGNORECASE)


def _stopwords() -> set[str]:
    return set(get_taxonomy()["stopwords"])


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in WORD_RE.finditer(text)]


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s and s.strip()]


def paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in PARAGRAPH_SPLIT_RE.split(text) if p and p.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def word_count(text: str) -> int:
    return len(tokenize(text))


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def syllable_count(word: str) -> int:
    groups = VOWEL_GROUP_RE.findall(word)
    count = len(groups)
    if word.lower().endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def flesch_reading_ease(text: str) -> float:
    """Approximate Flesch reading ease clipped to 0-100 (higher is easier)."""
    words = tokenize(text)
    sents = sentences(text)
    if not words or not sents:
        return 0.0
    avg_sentence_len = len(words) / len(sents)
    avg_syllables = sum(syllable_count(w) for w in words) / len(words)
    score = 206.835 - 1.015 * avg_sentence_len - 84.6 * avg_syllables
    return round(max(0.0, min(100.0, score)), 1)


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    """Frequency-based keyword and bigram extraction with stopword removal."""
    stop = _stopwords()
    # Keep positions so bigrams only join words that really sit next to each other in the text.
    tokens: list[str] = []
    bigrams: Counter[str] = Counter()
    for sentence in sentences(text) or [text]:
        positioned = [
            t if (len(t) >= 3 and t not in stop and not t.isdigit()) else None
            for t in tokenize(sentence)
        ]
        tokens.extend(t for t in positioned if t)
        # Bigrams never cross a sentence boundary.
        for a, b in zip(positioned, positioned[1:]):
            if a and b:
                bigrams[f"{a} {b}"] += 1
    if not tokens:
        return []
    unigrams = Counter(tokens)

    scored: dict[str, float] = {}
    for word, freq in unigrams.items():
        scored[word] = float(freq)
    for phrase, freq in bigrams.items():
        if freq >= 1:
            scored[phrase] = freq * 1.8 + 0.5

    # Boost known domain terms from the taxonomy.
    lowered = text.lower()
    for terms in get_taxonomy()["knowledge_categories"].values():
        for term in terms:
            if term in lowered and " " in term:
                scored[term] = scored.get(term, 0.0) + 2.0

    ranked = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))
    chosen: list[str] = []
    for phrase, _ in ranked:
        # Skip a single word already covered by a chosen phrase (e.g. "learning" inside "machine learning").
        if " " not in phrase and any(phrase in c.split() for c in chosen):
            continue
        if phrase in chosen:
            continue
        chosen.append(phrase)
        if len(chosen) >= limit:
            break
    return chosen


def _match_any(text_lower: str, terms: list[str]) -> int:
    hits = 0
    for term in terms:
        pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
        hits += len(re.findall(pattern, text_lower))
    return hits


def detect_category(text: str) -> tuple[str | None, dict[str, int]]:
    """Return the best knowledge category (or None) and the raw score table."""
    lowered = text.lower()
    scores: dict[str, int] = {}
    for category, terms in get_taxonomy()["knowledge_categories"].items():
        hits = _match_any(lowered, terms)
        if hits:
            scores[category] = hits
    if not scores:
        return None, {}
    best = max(scores.items(), key=lambda kv: (kv[1], kv[0]))[0]
    return best, scores


def detect_tone(text: str) -> str:
    lowered = text.lower()
    lexicon = get_taxonomy()["tone_lexicon"]
    scores = {tone: _match_any(lowered, terms) for tone, terms in lexicon.items()}
    best_tone, best_score = max(scores.items(), key=lambda kv: (kv[1], kv[0]))
    return best_tone if best_score > 0 else "professional"


def detect_emotion(text: str) -> str:
    lowered = text.lower()
    lexicon = get_taxonomy()["emotion_lexicon"]
    scores = {emo: _match_any(lowered, terms) for emo, terms in lexicon.items()}
    best, score = max(scores.items(), key=lambda kv: (kv[1], kv[0]))
    return best if score > 0 else "neutral"


def detect_post_type(text: str) -> str:
    lowered = text.lower()
    lexicon = get_taxonomy()["post_type_lexicon"]
    scores = {ptype: _match_any(lowered, terms) for ptype, terms in lexicon.items()}
    best, score = max(scores.items(), key=lambda kv: (kv[1], kv[0]))
    return best if score > 0 else "personal_story"


def detect_hook_type(first: str) -> str:
    """Classify the opening line. Returns 'statement' when no pattern matches."""
    candidate = first.strip().lower()
    for hook_type, pattern in get_taxonomy()["hook_patterns"].items():
        if re.search(pattern, candidate):
            return hook_type
    return "statement"


def hook_score(text: str) -> float:
    """Heuristic 0-1 strength of the opening line (not a reach prediction)."""
    first = first_line(text)
    if not first:
        return 0.0
    score = 0.0
    n = word_count(first)
    if 6 <= n <= 22:
        score += 0.3
    elif n <= 30:
        score += 0.15
    if detect_hook_type(first) != "statement":
        score += 0.25
    if "?" in first or re.search(r"\d", first):
        score += 0.15
    if re.search(r"\b(built|launched|finished|learned|failed|shipped|solved|won|completed)\b", first.lower()):
        score += 0.15
    if not first.lower().startswith(tuple(get_taxonomy()["generic_openers"])):
        score += 0.15
    else:
        score -= 0.1
    return round(max(0.0, min(1.0, score)), 2)


def detect_cta(text: str) -> str:
    """Classify the call to action using the last few lines of the post."""
    tail = " ".join(line for line in text.strip().splitlines() if line.strip())[-300:].lower()
    patterns = get_taxonomy()["cta_patterns"]
    for cta_type in ("question", "invite_comments", "share", "follow"):
        if re.search(patterns[cta_type], tail, flags=re.IGNORECASE):
            return cta_type
    return "none"


def detect_structure(text: str) -> list[str]:
    """Infer the post's structural roles from paragraph content, collapsing repeats."""
    roles_lexicon = get_taxonomy()["structure_roles"]
    blocks = paragraphs(text)
    roles: list[str] = []
    for index, block in enumerate(blocks):
        lowered = block.lower()
        if index == 0:
            role = "hook"
        elif index == len(blocks) - 1 and detect_cta(block) != "none":
            role = "cta"
        else:
            role = "context"
            best_score = 0
            for candidate, terms in roles_lexicon.items():
                score = _match_any(lowered, terms)
                if score > best_score:
                    role, best_score = candidate, score
        if not roles or roles[-1] != role:
            roles.append(role)
    if roles and roles[-1] != "cta" and detect_cta(text) != "none":
        roles.append("cta")
    return roles


def extract_hashtag_tags(text: str) -> list[str]:
    return [m.group(1) for m in HASHTAG_RE.finditer(text)]


def to_camel_concept(phrase: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[\s\-_/]+", phrase) if part)


def hashtag_concepts(text: str, keywords: list[str], limit: int = 5) -> list[str]:
    concepts: list[str] = []
    for tag in extract_hashtag_tags(text):
        if tag not in concepts:
            concepts.append(tag)
    for kw in keywords:
        concept = to_camel_concept(kw)
        if len(concept) >= 3 and concept not in concepts:
            concepts.append(concept)
        if len(concepts) >= limit:
            break
    return concepts[:limit]


def analyze_text(text: str) -> dict[str, Any]:
    """Full deterministic analysis of a post used by enhance/analyze endpoints."""
    category, _ = detect_category(text)
    keywords = extract_keywords(text)
    blocks = paragraphs(text)
    structure = detect_structure(text)
    hook_type = detect_hook_type(first_line(text))
    return {
        "post_type": detect_post_type(text),
        "topic": (category or (keywords[0] if keywords else "general")),
        "category": category,
        "tone": detect_tone(text),
        "emotion": detect_emotion(text),
        "keywords": keywords,
        "hook_type": hook_type,
        "hook_strength": hook_score(text),
        "structure": structure,
        "readability": flesch_reading_ease(text),
        "cta": detect_cta(text),
        "hashtags": extract_hashtag_tags(text),
        "length_words": word_count(text),
        "paragraph_count": len(blocks),
    }
