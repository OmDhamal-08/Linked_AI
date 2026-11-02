"""Subscription lifecycle. The user's `plan` column is the source of truth for access."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.payment_service import PaymentService


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class SubscriptionService:
    def __init__(self, repo: SubscriptionRepository, payments: PaymentService) -> None:
        self._repo = repo
        self._payments = payments

    def current(self, session: Session, user: User) -> dict[str, Any]:
        sub = self._repo.latest_for_user(session, user.id)
        return {
            "plan": user.plan,
            "status": sub.status if sub else "active",
            "provider": sub.provider if sub else self._payments.provider_name,
            "external_subscription_id": sub.external_subscription_id if sub else None,
            "started_at": _iso(sub.started_at) if sub else None,
            "expires_at": _iso(sub.expires_at) if sub else None,
        }

    def activate_premium(self, session: Session, user: User) -> dict[str, Any]:
        external_id = self._payments.start_subscription(user.id, "premium")
        now = datetime.now(timezone.utc)
        self._repo.add(
            session,
            user_id=user.id,
            plan="premium",
            status="active",
            provider=self._payments.provider_name,
            external_subscription_id=external_id,
            started_at=now,
            expires_at=now + timedelta(days=30),
        )
        user.plan = "premium"
        session.add(user)
        session.commit()
        return self.current(session, user)

    def cancel(self, session: Session, user: User) -> dict[str, Any]:
        sub: Subscription | None = self._repo.latest_for_user(session, user.id)
        if sub and sub.status == "active":
            self._payments.cancel_subscription(sub.external_subscription_id)
            sub.status = "canceled"
            session.add(sub)
        user.plan = "free"
        session.add(user)
        session.commit()
        return self.current(session, user)
