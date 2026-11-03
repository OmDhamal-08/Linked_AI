from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_app_container, get_current_user, rate_limit
from app.db.session import get_db
from app.models.user import User
from app.schemas.posts import AnalyzeRequest, EnhanceRequest, GenerateRequest, PostUpdate
from app.services.container import Container

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/generate", dependencies=[Depends(rate_limit("generate"))])
def generate_post(
    body: GenerateRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    """Create a post from structured input (RAG + LLM, plan-gated)."""
    return c.generation.generate(session, user, body)


@router.post("/enhance", dependencies=[Depends(rate_limit("enhance"))])
def enhance_post(
    body: EnhanceRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    """Analyse and improve an existing post."""
    return c.generation.enhance(session, user, body)


@router.post("/analyze", dependencies=[Depends(rate_limit("analyze"))])
def analyze_post(
    body: AnalyzeRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    """Deterministic analysis of a post (free). Advanced LLM review is Premium."""
    return c.generation.analyze(session, user, body)


@router.get("")
def list_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    post_type: str | None = Query(None, alias="type", pattern="^(generate|enhance)$"),
    category: str | None = Query(None, max_length=60),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return c.posts.list_posts(session, user, limit=limit, offset=offset, post_type=post_type, category=category)


@router.get("/{post_id}")
def get_post(
    post_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return c.posts.get_post(session, user, post_id)


@router.patch("/{post_id}")
def update_post(
    post_id: str,
    body: PostUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return c.posts.update_post(session, user, post_id, body)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    c.posts.delete_post(session, user, post_id)
    return Response(status_code=204)
