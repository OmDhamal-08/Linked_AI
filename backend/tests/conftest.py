"""Shared test fixtures. Environment variables are set BEFORE the app is imported."""

import os
import tempfile
import uuid
from pathlib import Path

_TMP_DIR = tempfile.mkdtemp(prefix="linkdine_tests_")
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{Path(_TMP_DIR) / 'test.db'}",
        "AUTO_CREATE_TABLES": "true",
        "JWT_SECRET": "test-secret-that-is-long-enough-for-hs256-1234",
        "AI_PROVIDER": "mock",
        "EMBEDDING_PROVIDER": "hashing",
        "EMBEDDING_DIM": "384",
        "FREE_FULL_POST_ENABLED": "false",
        "FREE_GENERATIONS_PER_DAY": "3",
        "FREE_ENHANCEMENTS_PER_DAY": "3",
        "RATE_LIMIT_PER_MINUTE": "10000",
        "ALLOW_MOCK_PAYMENTS": "true",
        "ADMIN_EMAILS": "admin@linkdine-test.com",
        "CORS_ORIGINS": "http://localhost:3000",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.db.base import Base  # noqa: E402
from app.db.session import ensure_schema, get_engine, get_session_factory  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.container import build_container, reset_container  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CSV = REPO_ROOT / "data" / "raw" / "synthetic_knowledge.csv"


@pytest.fixture(scope="session")
def client():
    Base.metadata.drop_all(get_engine())
    ensure_schema(get_engine())
    reset_container(build_container())
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def seeded(client):
    """Ingest the synthetic knowledge base once for the whole test session."""
    from app.services.container import get_container

    container = get_container()
    with get_session_factory()() as session:
        job = container.knowledge.ingest_upload(
            session, filename="synthetic_knowledge.csv", content=SYNTHETIC_CSV.read_bytes(), created_by=None
        )
    assert job["status"] == "completed"
    return job


def _signup(client, email_prefix: str = "user", email: str | None = None) -> dict:
    email = email or f"{email_prefix}-{uuid.uuid4().hex[:8]}@linkdine-test.com"
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongPassword123", "name": "Test User"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "email": email}


@pytest.fixture
def free_user(client):
    return _signup(client, "free")


@pytest.fixture
def premium_user(client):
    headers = _signup(client, "premium")
    response = client.post("/api/v1/subscription/mock-upgrade", headers=headers)
    assert response.status_code == 200, response.text
    return headers


@pytest.fixture
def admin_user(client):
    email = "admin@linkdine-test.com"
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPassword123"})
    if response.status_code == 200:
        return {"Authorization": f"Bearer {response.json()['access_token']}", "email": email}
    return _signup(client, email=email)


def generate_payload(**overrides) -> dict:
    payload = {
        "category": "achievement",
        "topic": "Machine Learning",
        "event": "Completed my first end-to-end machine learning project",
        "field": "AI/ML",
        "tone": "proud",
        "emotion": "happy",
        "audience": "students and developers",
        "length": "medium",
        "cta": "question",
        "keywords": ["machine learning", "AI", "learning journey"],
        "context": "Worked on the project for two months.",
    }
    payload.update(overrides)
    return payload


ENHANCE_TEXT = (
    "Excited to share that I finished my first machine learning model.\n\n"
    "I trained a classifier on a small dataset and compared the validation results with a baseline.\n\n"
    "The biggest lesson was that clean data matters more than a fancy architecture.\n\n"
    "What is your favourite way to learn machine learning?"
)
