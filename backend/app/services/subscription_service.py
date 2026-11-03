"""Subscription lifecycle. The user's `plan` column is the source of truth for access.

There is no payment gateway yet. `activate_premium` is the one place where a real
gateway (Stripe/Razorpay) would be called before switching the plan; until then it
only works when ALLOW_MOCK_PAYMENTS is on and we are not in production.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ForbiddenError
from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.subscription_repository import SubscriptionRepository

PROVIDER = "mock"
PREMIUM_DAYS = 30


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class SubscriptionService:
    def __init__(self, repo: SubscriptionRepository, settings: Settings) -> None:
        self._repo = repo
        self._settings = settings

    def current(self, session: Session, user: User) -> dict[str, Any]:
        sub = self._repo.latest_for_user(session, user.id)
        return {
            "plan": user.plan,
            "status": sub.status if sub else "active",
            "provider": sub.provider if sub else PROVIDER,
            "external_subscription_id": sub.external_subscription_id if sub else None,
            "started_at": _iso(sub.started_at) if sub else None,
            "expires_at": _iso(sub.expires_at) if sub else None,
        }

    def ensure_mock_allowed(self) -> None:
        if self._settings.is_production or not self._settings.allow_mock_payments:
            raise ForbiddenError("Mock payments are disabled in this environment.")

    def activate_premium(self, session: Session, user: User) -> dict[str, Any]:
        self.ensure_mock_allowed()
        now = datetime.now(timezone.utc)
        self._repo.add(
            session,
            user_id=user.id,
            plan="premium",
            status="active",
            provider=PROVIDER,
            external_subscription_id=f"mock_sub_{uuid.uuid4().hex[:12]}",
            started_at=now,
            expires_at=now + timedelta(days=PREMIUM_DAYS),
        )
        user.plan = "premium"
        session.add(user)
        session.commit()
        return self.current(session, user)

    def cancel(self, session: Session, user: User) -> dict[str, Any]:
        sub: Subscription | None = self._repo.latest_for_user(session, user.id)
        if sub and sub.status == "active":
            sub.status = "canceled"
            session.add(sub)
        user.plan = "free"
        session.add(user)
        session.commit()
        return self.current(session, user)
