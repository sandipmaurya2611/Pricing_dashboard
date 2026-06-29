from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime, date

from app.db import get_db
from app.middleware.tenant import get_tenant_ctx, TenantContext
from app.models.models import AuditLog, Product
from app.schemas.schemas import AuditLogOut, AuditListResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditListResponse)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    """Full audit trail, tenant-scoped, filterable."""
    query = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.product))
        .filter(AuditLog.org_id == ctx.org_id)
        .order_by(AuditLog.created_at.desc())
    )

    if product_id:
        query = query.filter(AuditLog.product_id == product_id)
    if status_filter:
        query = query.filter(AuditLog.execution_status == status_filter)
    if date_from:
        query = query.filter(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return AuditListResponse(items=[AuditLogOut.model_validate(i) for i in items], total=total)
