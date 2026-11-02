from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get(self, session: Session, user_id: str) -> User | None:
        return session.get(User, user_id)

    def get_by_email(self, session: Session, email: str) -> User | None:
        return session.scalar(select(User).where(User.email == email.lower()))

    def get_by_external_id(self, session: Session, external_id: str) -> User | None:
        return session.scalar(select(User).where(User.external_auth_id == external_id))

    def create(self, session: Session, **fields) -> User:
        user = User(**fields)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
