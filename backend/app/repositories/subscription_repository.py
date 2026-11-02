from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription import Subscription


class SubscriptionRepository:
    def latest_for_user(self, session: Session, user_id: str) -> Subscription | None:
        return session.scalar(
            select(Subscription).where(Subscription.user_id == user_id).order_by(Subscription.created_at.desc()).limit(1)
        )

    def add(self, session: Session, **fields) -> Subscription:
        row = Subscription(**fields)
        session.add(row)
        session.flush()
        return row
