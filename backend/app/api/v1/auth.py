from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_app_container, get_current_user, rate_limit
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginIn, ProfileIn, SignupIn, TokenOut, UserOut
from app.services.container import Container

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenOut, status_code=201, dependencies=[Depends(rate_limit("auth"))])
def signup(body: SignupIn, session: Session = Depends(get_db), c: Container = Depends(get_app_container)):
    return c.auth.signup(session, email=body.email, password=body.password, name=body.name)


@router.post("/login", response_model=TokenOut, dependencies=[Depends(rate_limit("auth"))])
def login(body: LoginIn, session: Session = Depends(get_db), c: Container = Depends(get_app_container)):
    return c.auth.login(session, email=body.email, password=body.password)


@router.post("/logout")
def logout(_user: User = Depends(get_current_user)):
    # Tokens are stateless; the client discards its token. Server-side revocation is a future addition.
    return {"status": "logged_out"}


@router.post("/profile", response_model=UserOut)
def update_profile(
    body: ProfileIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    updated = c.auth.update_profile(session, user, name=body.name, avatar_url=body.avatar_url)
    return UserOut.model_validate(updated)
