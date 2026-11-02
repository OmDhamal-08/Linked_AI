"""Usage limits, tracking and cost estimation."""

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import UsageLimitError
from app.models.user import User
from app.repositories.usage_repository import UsageRepository
from app.services.feature_access_service import FeatureAccessService


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


class UsageService:
    def __init__(self, repo: UsageRepository, access: FeatureAccessService, settings: Settings) -> None:
        self._repo = repo
        self._access = access
        self._settings = settings

    def used_today(self, session: Session, user_id: str, feature: str) -> int:
        return self._repo.count_for_day(session, user_id, feature, today_utc())

    def assert_available(self, session: Session, user: User, feature: str) -> None:
        limit = self._access.daily_limit(user.plan, feature)
        if self.used_today(session, user.id, feature) >= limit:
            raise UsageLimitError()

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        cost = (tokens_in / 1_000_000) * self._settings.ai_input_price_per_1m
        cost += (tokens_out / 1_000_000) * self._settings.ai_output_price_per_1m
        return round(cost, 6)

    def record(
        self,
        session: Session,
        user: User,
        *,
        feature: str,
        status: str,
        provider: str | None = None,
        model: str | None = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
        error_code: str | None = None,
    ) -> None:
        self._repo.add(
            session,
            user_id=user.id,
            feature=feature,
            request_date=today_utc(),
            tokens_used=tokens_in + tokens_out,
            estimated_cost=self.estimate_cost(tokens_in, tokens_out),
            status=status,
            provider=provider,
            model=model,
            error_code=error_code,
        )

    def summary(self, session: Session, user: User) -> dict[str, Any]:
        features: dict[str, Any] = {}
        for feature in ("generate", "enhance"):
            limit = self._access.daily_limit(user.plan, feature)
            used = self.used_today(session, user.id, feature)
            features[feature] = {"used": used, "limit": limit, "remaining": max(0, limit - used)}
        return {"date": today_utc().isoformat(), "plan": user.plan, "features": features}
