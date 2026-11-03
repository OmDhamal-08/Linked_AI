"""Email/password authentication.

Passwords are hashed with PBKDF2 (see core/security.py) and the API issues a
signed JWT on signup/login. Every protected route decodes that token to find the user.
"""

import re
from typing import Any

import jwt
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import InvalidRequestError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthService:
    def __init__(self, settings: Settings, users: UserRepository) -> None:
        self._settings = settings
        self._users = users

    def signup(self, session: Session, *, email: str, password: str, name: str | None) -> dict[str, Any]:
        email = self._normalise_email(email)
        if len(password) < 8:
            raise InvalidRequestError("Password must be at least 8 characters.")
        if self._users.get_by_email(session, email):
            raise InvalidRequestError("An account with this email already exists.")
        user = self._users.create(
            session,
            email=email,
            name=name,
            password_hash=hash_password(password),
            is_admin=email in self._settings.admin_email_list,
        )
        return self._issue(user)

    def login(self, session: Session, *, email: str, password: str) -> dict[str, Any]:
        email = self._normalise_email(email)
        user = self._users.get_by_email(session, email)
        # Same error for unknown email and wrong password, to avoid account enumeration.
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Email or password is incorrect.")
        return self._issue(user)

    def _issue(self, user: User) -> dict[str, Any]:
        token = create_access_token(
            user.id,
            secret=self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
            expires_minutes=self._settings.jwt_expire_minutes,
        )
        return {"access_token": token, "token_type": "bearer", "user_id": user.id}

    def user_from_token(self, session: Session, token: str) -> User:
        try:
            claims = decode_token(token, secret=self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Your session has expired. Please log in again.") from exc

        user = self._users.get(session, claims["sub"])
        if not user:
            raise UnauthorizedError("Your session is no longer valid. Please log in again.")
        return user

    def update_profile(self, session: Session, user: User, *, name: str | None, avatar_url: str | None) -> User:
        if name is not None:
            user.name = name.strip()[:120] or None
        if avatar_url is not None:
            user.avatar_url = avatar_url.strip()[:500] or None
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def require_user(self, session: Session, user_id: str) -> User:
        user = self._users.get(session, user_id)
        if not user:
            raise NotFoundError()
        return user

    @staticmethod
    def _normalise_email(email: str) -> str:
        cleaned = (email or "").strip().lower()
        if not EMAIL_RE.match(cleaned):
            raise InvalidRequestError("Please enter a valid email address.")
        return cleaned
