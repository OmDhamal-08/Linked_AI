from datetime import timedelta

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_app_container, require_admin
from app.core.errors import IngestionError
from app.db.session import get_db
from app.models.user import User
from app.services.container import Container
from app.services.usage_service import today_utc

router = APIRouter(prefix="/admin", tags=["admin"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/knowledge/ingest", status_code=201)
def ingest_dataset(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    """Upload a CSV or JSON dataset. Processed synchronously; returns the ingestion report."""
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise IngestionError("The file is larger than 10 MB.")
    return c.knowledge.ingest_upload(session, filename=file.filename or "upload", content=content, created_by=admin.id)


@router.get("/knowledge/stats")
def knowledge_stats(
    _admin: User = Depends(require_admin),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return c.knowledge.stats(session)


@router.get("/knowledge")
def list_knowledge(
    category: str | None = Query(None, max_length=60),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return c.knowledge.list_items(session, category=category, limit=limit, offset=offset)


@router.delete("/knowledge/{item_id}", status_code=204)
def delete_knowledge(
    item_id: str,
    _admin: User = Depends(require_admin),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    c.knowledge.delete_item(session, item_id)
    return Response(status_code=204)


@router.get("/ingestion-jobs")
def ingestion_jobs(
    _admin: User = Depends(require_admin),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    return {"items": c.knowledge.list_jobs(session)}


@router.get("/usage")
def usage_overview(
    days: int = Query(30, ge=1, le=365),
    _admin: User = Depends(require_admin),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    since = today_utc() - timedelta(days=days)
    return {"since": since.isoformat(), "rows": c.usage_repo.aggregate(session, since)}


@router.get("/errors")
def recent_errors(
    _admin: User = Depends(require_admin),
    session: Session = Depends(get_db),
    c: Container = Depends(get_app_container),
):
    rows = c.usage_repo.recent_errors(session)
    return {
        "items": [
            {
                "id": r.id,
                "feature": r.feature,
                "provider": r.provider,
                "model": r.model,
                "error_code": r.error_code,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }
