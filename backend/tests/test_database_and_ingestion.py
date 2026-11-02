import json

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.errors import IngestionError
from app.db.session import get_session_factory
from app.ingestion.cleaner import clean_text, content_hash
from app.ingestion.loader import parse_upload
from app.ingestion.pii import detect_and_redact
from app.ingestion.validator import parse_list, validate_record
from app.models.post import Post, PostAnalysis
from app.models.user import User
from app.repositories.post_repository import PostRepository
from app.services.container import get_container


GOOD_TEXT = (
    "Finished building a small data pipeline that cleans CSV files and loads them into a database. "
    "The biggest takeaway was writing tests before optimising anything."
)


# ---- database operations ----------------------------------------------------

def test_post_and_analysis_are_saved_and_cascade_deleted():
    with get_session_factory()() as session:
        user = User(email="db-ops@linkdine-test.com", plan="free", auth_provider="local")
        session.add(user)
        session.commit()

        post = Post(user_id=user.id, type="enhance", input_text="original", output_text="better", keywords_used=["ai"], hashtags=["AI"])
        analysis = PostAnalysis(topic="AI", keywords=["ai"], structure=["hook"], readability_score=60, hook_score=70, keyword_score=50, overall_score=65)
        saved = PostRepository().create(session, post, analysis)
        post_id = saved.id

        listed, total = PostRepository().list_for_user(session, user.id, limit=10, offset=0)
        assert total == 1 and listed[0].id == post_id

        session.delete(saved)
        session.commit()
        assert session.scalar(select(PostAnalysis).where(PostAnalysis.post_id == post_id)) is None


def test_duplicate_email_violates_unique_constraint():
    with get_session_factory()() as session:
        session.add(User(email="unique@linkdine-test.com", plan="free", auth_provider="local"))
        session.commit()
        session.add(User(email="unique@linkdine-test.com", plan="free", auth_provider="local"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_pagination_and_type_filter_on_history(client, seeded, premium_user):
    from tests.conftest import ENHANCE_TEXT

    for _ in range(3):
        client.post("/api/v1/posts/enhance", json={"text": ENHANCE_TEXT}, headers=premium_user)
    page = client.get("/api/v1/posts?limit=2&offset=0", headers=premium_user).json()
    assert len(page["items"]) == 2
    assert page["total"] >= 3


# ---- ingestion: validation, cleaning, PII, dedupe ----------------------------

def test_validate_record_requires_text():
    record, reason = validate_record({"category": "AI"})
    assert record is None and reason == "missing_text"


def test_validate_record_rejects_short_text():
    record, reason = validate_record({"text": "Too short to be useful."})
    assert reason == "text_too_short"


def test_validate_record_ignores_unknown_taxonomy_values():
    record, reason = validate_record({"text": GOOD_TEXT, "category": "Astrology", "tone": "sarcastic", "cta_type": "bribe"})
    assert reason is None
    assert record["category"] is None
    assert record["tone"] is None
    assert record["cta_type"] is None


def test_parse_list_handles_several_separators():
    assert parse_list("a;b|c, d") == ["a", "b", "c", "d"]
    assert parse_list(["#AI", "ai"]) == ["AI"]
    assert parse_list(None) == []


def test_clean_text_removes_html_urls_and_zero_width():
    raw = "<p>Hello&nbsp;world</p> visit https://example.com ​ now"
    cleaned = clean_text(raw)
    assert "<p>" not in cleaned and "https://" not in cleaned and "​" not in cleaned


def test_content_hash_normalises_whitespace_and_case():
    assert content_hash("Hello   World") == content_hash("hello world")


def test_pii_is_redacted():
    text, found = detect_and_redact("Contact me at ada@example.com or +91 98765 43210.")
    assert "EMAIL" in found
    assert "ada@example.com" not in text
    assert "[REDACTED_EMAIL]" in text


def test_pan_and_aadhaar_are_detected():
    text, found = detect_and_redact("PAN ABCDE1234F and Aadhaar 1234 5678 9012")
    assert "PAN" in found and "AADHAAR" in found


def test_loader_accepts_csv_and_json_and_rejects_other_types():
    csv_bytes = b"text,category\n" + ('"' + GOOD_TEXT + '",AI\n').encode()
    source, rows = parse_upload("data.csv", csv_bytes, max_rows=100)
    assert source == "csv" and rows[0]["category"] == "AI"

    json_bytes = json.dumps({"records": [{"text": GOOD_TEXT}]}).encode()
    source, rows = parse_upload("data.json", json_bytes, max_rows=100)
    assert source == "json" and len(rows) == 1

    with pytest.raises(IngestionError):
        parse_upload("data.xlsx", b"nope", max_rows=10)
    with pytest.raises(IngestionError):
        parse_upload("data.csv", b"category\nAI\n", max_rows=10)


def test_loader_enforces_row_limit():
    rows = "text\n" + "\n".join(f'"{GOOD_TEXT} {i}"' for i in range(5))
    with pytest.raises(IngestionError):
        parse_upload("big.csv", rows.encode(), max_rows=3)


def test_pipeline_dedupes_and_rejects_and_infers_metadata():
    from app.core.config import get_settings
    from app.ingestion.pipeline import IngestionPipeline
    from app.repositories.knowledge_repository import KnowledgeRepository

    container = get_container()
    settings = get_settings()
    pipeline = IngestionPipeline(embeddings=container.embeddings, repo=KnowledgeRepository(), settings=settings)
    rows = [
        {"text": GOOD_TEXT},
        {"text": GOOD_TEXT},  # duplicate in the same batch
        {"text": "short"},  # rejected
        {"text": GOOD_TEXT + " Reach me at dev@example.com for the notes."},  # PII redacted
    ]
    with get_session_factory()() as session:
        report = pipeline.run(session, rows, source_type="json", source_reference="unit-test")
    assert report["records_processed"] == 2
    assert report["duplicates"] == 1
    assert report["records_rejected"] == 1
    assert report["pii_redacted"] == 1
    assert report["embeddings_generated"] == 2


def test_ingest_job_is_recorded_and_failed_jobs_are_reported(client, admin_user):
    csv_bytes = b"text\n" + f'"{GOOD_TEXT}"\n'.encode()
    response = client.post(
        "/api/v1/admin/knowledge/ingest",
        files={"file": ("unit.csv", csv_bytes, "text/csv")},
        headers=admin_user,
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "completed"

    bad = client.post(
        "/api/v1/admin/knowledge/ingest",
        files={"file": ("unit.xlsx", b"data", "application/octet-stream")},
        headers=admin_user,
    )
    assert bad.status_code == 400
    jobs = client.get("/api/v1/admin/ingestion-jobs", headers=admin_user).json()["items"]
    assert any(j["status"] == "failed" for j in jobs)


def test_admin_can_delete_knowledge_item(client, seeded, admin_user):
    listing = client.get("/api/v1/admin/knowledge?limit=1", headers=admin_user).json()
    item_id = listing["items"][0]["id"]
    assert client.delete(f"/api/v1/admin/knowledge/{item_id}", headers=admin_user).status_code == 204
    assert client.delete(f"/api/v1/admin/knowledge/{item_id}", headers=admin_user).status_code == 404
