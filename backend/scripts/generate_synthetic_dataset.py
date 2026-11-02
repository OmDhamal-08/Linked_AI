"""Generates SYNTHETIC development data (no third-party posts are used or copied).

Outputs:
  data/raw/synthetic_knowledge.csv   knowledge records (some metadata left blank on purpose,
                                     so the NLP pipeline must fill it in)
  evaluation/test_queries.json       evaluation queries with expected category/tone/keywords

Usage (from backend/):  python scripts/generate_synthetic_dataset.py
"""

import csv
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
RAW_PATH = BACKEND / "data" / "raw" / "synthetic_knowledge.csv"
EVAL_PATH = BACKEND / "evaluation" / "test_queries.json"

# category -> list of (topic, keywords, tone, hook_type, structure, audience)
TOPICS: dict[str, list[tuple[str, list[str], str, str, str, str]]] = {
    "AI": [
        ("LLM application", ["llm", "prompt", "application", "ai"], "educational", "lesson", "hook|context|learning|cta", "developers"),
        ("AI assistants", ["ai", "assistant", "workflow", "automation"], "proud", "achievement", "hook|achievement|learning|cta", "professionals"),
        ("Generative AI", ["generative", "ai", "content", "evaluation"], "reflective", "story", "hook|context|reflection|cta", "students"),
    ],
    "Machine Learning": [
        ("Machine learning project", ["machine learning", "model", "training", "project"], "proud", "achievement", "hook|context|achievement|learning|cta", "students and developers"),
        ("Model evaluation", ["model", "evaluation", "metrics", "validation"], "educational", "lesson", "hook|problem|solution|learning|cta", "students"),
        ("Neural networks", ["neural", "networks", "training", "deep learning"], "humble", "curiosity", "hook|context|learning|cta", "developers"),
    ],
    "Data Science": [
        ("Data analysis", ["data", "analysis", "dashboard", "insights"], "professional", "achievement", "hook|context|achievement|learning|cta", "professionals"),
        ("Exploratory analysis", ["pandas", "data", "statistics", "dataset"], "educational", "lesson", "hook|context|learning|cta", "students"),
        ("Data visualization", ["visualization", "data", "dashboard", "charts"], "excited", "milestone", "hook|achievement|cta", "recruiters"),
    ],
    "Backend Development": [
        ("REST API design", ["api", "endpoint", "fastapi", "backend"], "educational", "lesson", "hook|problem|solution|learning|cta", "developers"),
        ("Database optimization", ["database", "query", "index", "backend"], "proud", "achievement", "hook|context|achievement|learning|cta", "developers"),
        ("Authentication service", ["authentication", "backend", "api", "security"], "professional", "achievement", "hook|achievement|learning|cta", "developers"),
    ],
    "Frontend Development": [
        ("React components", ["react", "components", "frontend", "ui"], "excited", "achievement", "hook|achievement|learning|cta", "developers"),
        ("Accessible forms", ["accessibility", "forms", "frontend", "ui"], "educational", "lesson", "hook|learning|cta", "developers"),
        ("Responsive layouts", ["responsive", "css", "tailwind", "layout"], "conversational", "story", "hook|context|learning|cta", "students"),
    ],
    "Software Engineering": [
        ("Code review practice", ["code review", "engineering", "testing", "quality"], "reflective", "lesson", "hook|context|learning|reflection|cta", "developers"),
        ("Refactoring legacy code", ["refactor", "code", "architecture", "engineering"], "humble", "story", "hook|problem|solution|learning|cta", "developers"),
        ("Automated testing", ["testing", "tests", "software", "quality"], "professional", "achievement", "hook|achievement|learning|cta", "professionals"),
    ],
    "DevOps": [
        ("CI/CD pipeline", ["ci/cd", "pipeline", "deployment", "devops"], "proud", "achievement", "hook|context|achievement|learning|cta", "developers"),
        ("Container deployment", ["docker", "containers", "deployment", "devops"], "educational", "lesson", "hook|problem|solution|learning|cta", "developers"),
        ("Monitoring setup", ["monitoring", "logs", "alerts", "devops"], "professional", "milestone", "hook|achievement|cta", "professionals"),
    ],
    "Cloud": [
        ("Serverless deployment", ["serverless", "cloud", "aws", "functions"], "excited", "achievement", "hook|achievement|learning|cta", "developers"),
        ("Cloud cost review", ["cloud", "cost", "aws", "architecture"], "educational", "lesson", "hook|learning|cta", "professionals"),
        ("Cloud certification", ["cloud", "certification", "aws", "study"], "proud", "achievement", "hook|achievement|cta", "students"),
    ],
    "Cybersecurity": [
        ("Secure coding", ["security", "encryption", "vulnerability", "coding"], "educational", "lesson", "hook|problem|solution|learning|cta", "developers"),
        ("Phishing awareness", ["phishing", "security", "awareness", "threat"], "professional", "lesson", "hook|learning|cta", "general audience"),
        ("Penetration testing practice", ["pentest", "security", "vulnerability", "lab"], "excited", "achievement", "hook|achievement|learning|cta", "students"),
    ],
    "Web Development": [
        ("Personal website", ["website", "web development", "html", "javascript"], "proud", "achievement", "hook|achievement|learning|cta", "students"),
        ("Web performance", ["web", "performance", "javascript", "loading"], "educational", "lesson", "hook|learning|cta", "developers"),
        ("Progressive web app", ["web", "app", "javascript", "offline"], "excited", "milestone", "hook|achievement|cta", "developers"),
    ],
    "Career": [
        ("Job search journey", ["job", "search", "career", "applications"], "grateful", "story", "hook|context|reflection|cta", "professionals"),
        ("Interview preparation", ["interview", "career", "practice", "preparation"], "humble", "lesson", "hook|problem|solution|learning|cta", "students"),
        ("New role announcement", ["career", "role", "team", "growth"], "grateful", "achievement", "hook|achievement|reflection|cta", "professionals"),
    ],
    "Internship": [
        ("Summer internship", ["internship", "intern", "team", "learning"], "grateful", "story", "hook|context|reflection|cta", "students"),
        ("Intern project delivery", ["intern", "project", "delivery", "mentor"], "proud", "achievement", "hook|achievement|learning|cta", "students"),
        ("Internship lessons", ["internship", "lessons", "feedback", "growth"], "reflective", "lesson", "hook|learning|cta", "students"),
    ],
    "Student": [
        ("Semester project", ["student", "project", "semester", "course"], "proud", "achievement", "hook|context|achievement|learning|cta", "students"),
        ("Study routine", ["study", "course", "exam", "routine"], "humble", "lesson", "hook|learning|cta", "students"),
        ("University hackathon", ["university", "hackathon", "team", "student"], "excited", "achievement", "hook|achievement|cta", "students"),
    ],
    "Leadership": [
        ("Mentoring teammates", ["mentoring", "leadership", "team", "growth"], "grateful", "story", "hook|context|reflection|cta", "professionals"),
        ("Leading a team", ["team lead", "leadership", "team", "delivery"], "confident", "lesson", "hook|problem|solution|learning|cta", "professionals"),
        ("Running a retrospective", ["leadership", "retrospective", "team", "feedback"], "reflective", "lesson", "hook|learning|cta", "professionals"),
    ],
    "Entrepreneurship": [
        ("Startup prototype", ["startup", "prototype", "founder", "product"], "excited", "achievement", "hook|context|achievement|learning|cta", "founders"),
        ("Product launch", ["product launch", "startup", "users", "feedback"], "proud", "milestone", "hook|achievement|cta", "founders"),
        ("Founder lessons", ["founder", "startup", "customers", "lesson"], "humble", "lesson", "hook|problem|solution|learning|cta", "founders"),
    ],
}

SENTENCES = {
    "achievement": "I finished {topic_l} this month and it works end to end. The main outcome: {kw}.",
    "lesson": "Working on {topic_l} taught me one clear lesson about {kw}. Small experiments beat big plans.",
    "story": "It started as a small idea about {topic_l}. Over time the work turned into something practical around {kw}.",
    "curiosity": "Most people only see the final result of {topic_l}. The real learning is in the process around {kw}.",
    "milestone": "A checkpoint for {topic_l}: the team shipped the first working version focused on {kw}.",
}
CONTEXT_LINE = "The focus was on {kw_join}, with regular reviews and honest feedback along the way."
REFLECTION_LINE = "Looking back, the process mattered as much as the outcome."
CTA_LINES = [
    "What part of {topic_l} would you explore next?",
    "Share your experience with {topic_l} in the comments.",
    "Feel free to share this with someone who is starting out.",
]


def _record_text(topic: str, keywords: list[str], hook: str, variant: int) -> str:
    base_key = {"lesson": "lesson", "story": "story", "curiosity": "curiosity", "milestone": "milestone"}.get(hook, "achievement")
    kw_main = keywords[0]
    # Lower-case the first letter only for ordinary words (keep acronyms such as "LLM" intact).
    topic_l = topic if topic[:2].isupper() else topic[0].lower() + topic[1:]
    parts = [
        SENTENCES[base_key].format(topic_l=topic_l, kw=kw_main),
        CONTEXT_LINE.format(kw_join=", ".join(keywords[:3])),
        REFLECTION_LINE if variant % 2 == 0 else "The next step is to repeat the cycle with clearer goals.",
        CTA_LINES[variant % len(CTA_LINES)].format(topic_l=topic_l),
    ]
    return " ".join(parts)


def build_records() -> list[dict]:
    rows: list[dict] = []
    idx = 0
    for category, topics in TOPICS.items():
        for topic, keywords, tone, hook_type, structure, audience in topics:
            for variant in range(3):
                idx += 1
                blank = idx % 4 == 0  # leave some metadata empty so the pipeline must generate it
                rows.append(
                    {
                        "id": idx,
                        "category": "" if blank else category,
                        "topic": topic,
                        "text": _record_text(topic, keywords, hook_type, variant + idx),
                        "keywords": "" if blank else ";".join(keywords),
                        "tone": "" if idx % 5 == 0 else tone,
                        "hook_type": "" if blank else hook_type,
                        "structure": "" if idx % 3 == 0 else structure.replace("|", ";"),
                        "hashtags": "",
                        "audience": audience,
                    }
                )
    return rows


def build_eval_queries(rows: list[dict]) -> list[dict]:
    """One evaluation query per category per topic (plus variants), with expected labels."""
    queries: list[dict] = []
    for category, topics in TOPICS.items():
        for topic, keywords, tone, hook_type, _structure, audience in topics:
            queries.append(
                {
                    "query": f"{topic} with {keywords[0]} and {keywords[1]} sharing a {tone} post",
                    "category": category,
                    "topic": topic,
                    "tone": tone,
                    "relevant_keywords": keywords[:2],
                    "expected_hook_type": hook_type,
                    "audience": audience,
                }
            )
            queries.append(
                {
                    "query": f"I want to write about {topic.lower()} for {audience}",
                    "category": category,
                    "topic": topic,
                    "tone": tone,
                    "relevant_keywords": keywords[:1],
                    "expected_hook_type": hook_type,
                    "audience": audience,
                }
            )
    return queries


def main() -> None:
    rows = build_records()
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    queries = build_eval_queries(rows)
    EVAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVAL_PATH.write_text(json.dumps({"queries": queries}, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} knowledge records to {RAW_PATH}")
    print(f"Wrote {len(queries)} evaluation queries to {EVAL_PATH}")


if __name__ == "__main__":
    main()
