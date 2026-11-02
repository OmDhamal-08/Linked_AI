from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_app_container, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.container import Container

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get("")
def current_subscription(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return c.subscriptions.current(session, user)


@router.post("/mock-upgrade")
def mock_upgrade(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    """Development only: activate Premium without a real payment."""
    c.payments.ensure_mock_allowed()
    return c.subscriptions.activate_premium(session, user)


@router.post("/cancel")
def cancel_subscription(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return c.subscriptions.cancel(session, user)
