import pytest

from app.core.errors import ForbiddenError
from app.db.session import get_session_factory
from app.core.config import Settings
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.subscription_service import SubscriptionService
from tests.conftest import ENHANCE_TEXT, generate_payload


def test_free_generation_limit_is_enforced(client, seeded):
    from tests.conftest import _signup

    headers = _signup(client, "limit")
    for _ in range(3):
        assert client.post("/api/v1/posts/generate", json=generate_payload(), headers=headers).status_code == 200
    blocked = client.post("/api/v1/posts/generate", json=generate_payload(), headers=headers)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "usage_limit_reached"


def test_enhance_limit_is_separate_from_generate_limit(client, seeded):
    from tests.conftest import _signup

    headers = _signup(client, "limit-sep")
    for _ in range(3):
        client.post("/api/v1/posts/generate", json=generate_payload(), headers=headers)
    # Generate quota is exhausted, but enhance quota is still available.
    assert client.post("/api/v1/posts/enhance", json={"text": ENHANCE_TEXT}, headers=headers).status_code == 200


def test_usage_endpoint_reports_remaining(client, seeded):
    from tests.conftest import _signup

    headers = _signup(client, "usage")
    client.post("/api/v1/posts/generate", json=generate_payload(), headers=headers)
    usage = client.get("/api/v1/usage", headers=headers).json()
    assert usage["plan"] == "free"
    assert usage["features"]["generate"]["used"] == 1
    assert usage["features"]["generate"]["remaining"] == 2
    assert usage["features"]["generate"]["limit"] == 3


def test_premium_is_not_limited_by_free_quota(client, seeded, premium_user):
    for _ in range(4):
        response = client.post("/api/v1/posts/generate", json=generate_payload(), headers=premium_user)
        assert response.status_code == 200
    usage = client.get("/api/v1/usage", headers=premium_user).json()
    assert usage["plan"] == "premium"
    assert usage["features"]["generate"]["limit"] > 3


def test_failed_generation_is_logged_as_failed_usage(client, seeded, premium_user, monkeypatch):
    from app.ai.base import AIProvider, AIRequest, AIResult, ProviderError
    from app.services.container import get_container

    class Broken(AIProvider):
        name = "broken"
        model = "broken"

        def complete(self, request: AIRequest) -> AIResult:
            raise ProviderError("down")

    container = get_container()
    monkeypatch.setattr(container.ai, "primary", Broken())
    monkeypatch.setattr(container.ai, "fallback", None)
    from sqlalchemy import func, select

    from app.models.usage import UsageLog

    with get_session_factory()() as session:
        before = session.scalar(select(func.count()).where(UsageLog.status == "failed")) or 0
    response = client.post("/api/v1/posts/generate", json=generate_payload(), headers=premium_user)
    assert response.status_code == 503
    with get_session_factory()() as session:
        after = session.scalar(select(func.count()).where(UsageLog.status == "failed")) or 0
    assert after == before + 1


def test_subscription_status_for_free_user(client, free_user):
    response = client.get("/api/v1/subscription", headers=free_user)
    assert response.status_code == 200
    assert response.json()["plan"] == "free"


def test_mock_upgrade_then_cancel(client):
    from tests.conftest import _signup

    headers = _signup(client, "sub")
    upgraded = client.post("/api/v1/subscription/mock-upgrade", headers=headers)
    assert upgraded.status_code == 200
    assert upgraded.json()["plan"] == "premium"
    assert upgraded.json()["external_subscription_id"].startswith("mock_sub_")
    assert client.get("/api/v1/users/me", headers=headers).json()["plan"] == "premium"

    canceled = client.post("/api/v1/subscription/cancel", headers=headers)
    assert canceled.json()["plan"] == "free"
    assert client.get("/api/v1/users/me", headers=headers).json()["plan"] == "free"


def test_mock_payments_are_blocked_in_production():
    service = SubscriptionService(SubscriptionRepository(), Settings(environment="production", allow_mock_payments=True))
    with pytest.raises(ForbiddenError):
        service.ensure_mock_allowed()


def test_mock_payments_can_be_disabled_outside_production():
    service = SubscriptionService(SubscriptionRepository(), Settings(environment="development", allow_mock_payments=False))
    with pytest.raises(ForbiddenError):
        service.ensure_mock_allowed()


def test_feature_access_is_driven_by_plan_not_ui():
    from app.core.config import get_settings
    from app.services.feature_access_service import FeatureAccessService

    access = FeatureAccessService(get_settings())
    assert access.can("premium", "generate_full_post") is True
    assert access.can("free", "enhance_full_post") is False
    assert access.can("free", "post_variations") is False
    assert access.max_variations("free") == 1
    assert access.max_variations("premium") >= 2
