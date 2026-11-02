"""Ingest CSV/JSON knowledge datasets from data/raw/ (or a given file) into the knowledge base.

Usage (from backend/):
    python scripts/ingest_dataset.py                 # every .csv/.json in data/raw/
    python scripts/ingest_dataset.py path/to/file.csv
"""

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.db.session import ensure_schema, get_engine, get_session_factory  # noqa: E402
from app.ingestion.loader import parse_upload  # noqa: E402
from app.services.container import build_container, reset_container  # noqa: E402

RAW_DIR = BACKEND / "data" / "raw"


def collect_files(target: str | None) -> list[Path]:
    if target:
        return [Path(target)]
    return sorted(p for p in RAW_DIR.glob("*") if p.suffix.lower() in {".csv", ".json"})


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest knowledge datasets")
    parser.add_argument("path", nargs="?", help="Optional file to ingest (defaults to data/raw/*)")
    args = parser.parse_args()

    files = collect_files(args.path)
    if not files:
        print(f"No .csv or .json files found in {RAW_DIR}. Add a dataset and run again.")
        return 1

    ensure_schema(get_engine())
    container = build_container()
    reset_container(container)
    summary = []
    with get_session_factory()() as session:
        for path in files:
            content = path.read_bytes()
            try:
                job = container.knowledge.ingest_upload(
                    session, filename=path.name, content=content, created_by=None
                )
            except Exception as exc:  # noqa: BLE001 - report and continue with the next file
                summary.append({"file": path.name, "status": "failed", "error": getattr(exc, "message", str(exc))})
                continue
            summary.append({"file": path.name, **{k: job[k] for k in (
                "status", "records_uploaded", "records_processed", "records_rejected",
                "duplicates", "embeddings_generated", "pii_redacted")}})
    print(json.dumps(summary, indent=2))
    return 0 if all(s["status"] == "completed" for s in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
