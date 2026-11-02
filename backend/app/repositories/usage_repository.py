from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.usage import UsageLog


class UsageRepository:
    def count_for_day(self, session: Session, user_id: str, feature: str, day: date) -> int:
        stmt = select(func.count()).where(
            UsageLog.user_id == user_id,
            UsageLog.feature == feature,
            UsageLog.request_date == day,
            UsageLog.status != "rejected",
        )
        return int(session.scalar(stmt) or 0)

    def add(self, session: Session, **fields) -> UsageLog:
        row = UsageLog(**fields)
        session.add(row)
        session.commit()
        return row

    def aggregate(self, session: Session, since: date) -> list[dict]:
        stmt = (
            select(
                UsageLog.request_date,
                UsageLog.feature,
                UsageLog.provider,
                UsageLog.status,
                func.count().label("requests"),
                func.sum(UsageLog.tokens_used).label("tokens"),
                func.sum(UsageLog.estimated_cost).label("cost"),
            )
            .where(UsageLog.request_date >= since)
            .group_by(UsageLog.request_date, UsageLog.feature, UsageLog.provider, UsageLog.status)
            .order_by(UsageLog.request_date.desc())
        )
        return [
            {
                "date": r.request_date.isoformat(),
                "feature": r.feature,
                "provider": r.provider,
                "status": r.status,
                "requests": int(r.requests),
                "tokens": int(r.tokens or 0),
                "estimated_cost": round(float(r.cost or 0.0), 6),
            }
            for r in session.execute(stmt).all()
        ]

    def recent_errors(self, session: Session, limit: int = 50) -> list[UsageLog]:
        stmt = select(UsageLog).where(UsageLog.status == "failed").order_by(UsageLog.created_at.desc()).limit(limit)
        return list(session.scalars(stmt).all())
