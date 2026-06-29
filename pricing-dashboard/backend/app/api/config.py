from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db
from app.middleware.tenant import get_tenant_ctx, require_admin, TenantContext
from app.models.models import OrgConfig, Organization
from app.schemas.schemas import OrgConfigOut, OrgConfigUpdate

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=OrgConfigOut)
def get_config(
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    """Get current org configuration."""
    config = db.query(OrgConfig).filter(OrgConfig.org_id == ctx.org_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return OrgConfigOut.model_validate(config)


@router.put("", response_model=OrgConfigOut)
def update_config(
    data: OrgConfigUpdate,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(require_admin),
):
    """Update org config (admin only)."""
    config = db.query(OrgConfig).filter(OrgConfig.org_id == ctx.org_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return OrgConfigOut.model_validate(config)


@router.get("/org-info")
def get_org_info(
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    """Get organization info including invite code."""
    org = db.query(Organization).filter(Organization.id == ctx.org_id).first()
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "invite_code": org.invite_code,
        "created_at": org.created_at,
    }
