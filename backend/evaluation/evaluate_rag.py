"""RAG evaluation harness.

Runs every query in evaluation/test_queries.json through the real query analyzer and
retriever, then reports:
  - Precision@K : share of the top-K results whose knowledge category matches the expected one
  - Hit@K       : share of queries where at least one top-K result matches the category
  - Topic relevance, Tone alignment, Keyword relevance (share of top-K items sharing a relevant keyword)

Use it to compare embedding models, K values, chunking, prompts or rerankers.
These numbers are only meaningful on a real knowledge base; the bundled synthetic dataset is for development.

Usage (from backend/, after ingesting data):
    python evaluation/evaluate_rag.py --k 5
    python evaluation/evaluate_rag.py --k 3 --report evaluation/report_k3.json
"""

import argparse
import json
import sys
from pathlib import Path
from statistics import mean

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.db.session import get_session_factory  # noqa: E402
from app.nlp.analysis import detect_category, extract_keywords  # noqa: E402
from app.rag.query_builder import AnalyzedQuery  # noqa: E402
from app.rag.retriever import Retriever  # noqa: E402
from app.services.container import build_container, reset_container  # noqa: E402

QUERIES_PATH = Path(__file__).with_name("test_queries.json")


def evaluate(k: int, limit: int | None = None) -> dict:
    container = build_container()
    reset_container(container)
    retriever = Retriever(container.vector_store, container.embeddings, container.settings)
    queries = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))["queries"][:limit]

    per_query = []
    with get_session_factory()() as session:
        for q in queries:
            detected_category, _ = detect_category(q["query"])
            keywords = list(dict.fromkeys(q.get("relevant_keywords", []) + extract_keywords(q["query"], 4)))
            analyzed = AnalyzedQuery(
                semantic_query=f"{q['topic']} {q['query']} LinkedIn post",
                knowledge_category=detected_category,
                keywords=keywords,
                tone=q["tone"],
            )
            result = retriever.retrieve(session, analyzed, top_k=k)
            items = result.items
            hits = [i for i in items if i["category"] == q["category"]]
            relevant_kw = {kw.lower() for kw in q.get("relevant_keywords", [])}
            kw_hits = [i for i in items if relevant_kw & {x.lower() for x in i["keywords"]}]
            per_query.append(
                {
                    "query": q["query"],
                    "expected_category": q["category"],
                    "detected_category": detected_category,
                    "precision_at_k": len(hits) / max(1, len(items)),
                    "hit_at_k": 1.0 if hits else 0.0,
                    "topic_relevance": 1.0 if any(i["topic"] == q["topic"] for i in items) else 0.0,
                    "tone_alignment": sum(1 for i in items if i["tone"] == q["tone"]) / max(1, len(items)),
                    "keyword_relevance": len(kw_hits) / max(1, len(items)),
                    "returned": len(items),
                }
            )

    summary = {
        "k": k,
        "queries": len(per_query),
        "embedding_provider": container.embeddings.provider_name,
        "embedding_model": container.embeddings.model,
        "vector_store": container.vector_store.name,
        "precision_at_k": round(mean(r["precision_at_k"] for r in per_query), 3) if per_query else 0.0,
        "hit_at_k": round(mean(r["hit_at_k"] for r in per_query), 3) if per_query else 0.0,
        "topic_relevance": round(mean(r["topic_relevance"] for r in per_query), 3) if per_query else 0.0,
        "tone_alignment": round(mean(r["tone_alignment"] for r in per_query), 3) if per_query else 0.0,
        "keyword_relevance": round(mean(r["keyword_relevance"] for r in per_query), 3) if per_query else 0.0,
    }
    return {"summary": summary, "per_query": per_query}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval quality")
    parser.add_argument("--k", type=int, default=5, help="Top-K to evaluate")
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N queries")
    parser.add_argument("--report", default=str(Path(__file__).with_name("report.json")))
    args = parser.parse_args()

    report = evaluate(args.k, args.limit)
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Per-query details written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
