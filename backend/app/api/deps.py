from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ForbiddenError, RateLimitError, UnauthorizedError
from app.core.rate_limit import SlidingWindowRateLimiter
from app.db.session import get_db
from app.models.user import User
from app.services.container import Container, get_container

bearer_scheme = HTTPBearer(auto_error=False)
_limiter: SlidingWindowRateLimiter | None = None


def get_limiter() -> SlidingWindowRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = SlidingWindowRateLimiter(get_settings().rate_limit_per_minute)
    return _limiter


def reset_limiter() -> None:
    global _limiter
    _limiter = None


def get_app_container() -> Container:
    return get_container()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
    container: Container = Depends(get_app_container),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    user = container.auth.user_from_token(session, credentials.credentials)
    request.state.user_id = user.id
    return user


def require_admin(user: User = Depends(get_current_user), container: Container = Depends(get_app_container)) -> User:
    if not (user.is_admin or user.email in container.settings.admin_email_list):
        raise ForbiddenError()
    return user


def rate_limit(scope: str) -> Callable[[Request], None]:
    """Per-client-IP sliding-window limit for a route group. Raises RateLimitError when exceeded."""

    def checker(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        if not get_limiter().hit(f"{scope}:{client}"):
            raise RateLimitError()

    return checker
