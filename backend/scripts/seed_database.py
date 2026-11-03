"""Development seeding: creates tables, a demo user (free plan) and knowledge data.

Refuses to run in production. Usage (from backend/):
    python scripts/seed_database.py
"""

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import func, select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import ensure_schema, get_engine, get_session_factory  # noqa: E402
from app.models.knowledge import KnowledgeItem  # noqa: E402
from app.models.user import User  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.services.container import build_container, reset_container  # noqa: E402

RAW_DIR = BACKEND / "data" / "raw"


def main() -> int:
    settings = get_settings()
    if settings.is_production:
        print("Refusing to seed a production database.")
        return 1

    ensure_schema(get_engine())
    container = build_container(settings)
    reset_container(container)

    with get_session_factory()() as session:
        demo = session.scalar(select(User).where(User.email == settings.demo_user_email.lower()))
        if demo is None:
            session.add(
                User(
                    email=settings.demo_user_email.lower(),
                    name="Demo User",
                    plan="free",
                    password_hash=hash_password(settings.demo_user_password),
                )
            )
            session.commit()
            print(f"Created demo user {settings.demo_user_email} (free plan).")
        else:
            print(f"Demo user {settings.demo_user_email} already exists.")

        existing = session.scalar(select(func.count()).select_from(KnowledgeItem)) or 0
        if existing == 0:
            for path in sorted(RAW_DIR.glob("*")):
                if path.suffix.lower() not in {".csv", ".json"}:
                    continue
                job = container.knowledge.ingest_upload(
                    session, filename=path.name, content=path.read_bytes(), created_by=None
                )
                print(json.dumps({"file": path.name, "status": job["status"], "processed": job["records_processed"]}))
        else:
            print(f"Knowledge base already has {existing} records; skipping ingestion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
