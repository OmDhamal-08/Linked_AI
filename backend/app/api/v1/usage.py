from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_app_container, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.container import Container

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("")
def usage(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return c.usage.summary(session, user)
