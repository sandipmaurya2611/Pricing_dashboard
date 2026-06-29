from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dataclasses import dataclass
from typing import Optional

from app.core.security import decode_access_token
from app.db import get_db
from app.models.models import User, UserRole

security = HTTPBearer()


@dataclass
class TenantContext:
    user_id: str
    org_id: str
    role: UserRole
    user: User


def get_tenant_ctx(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> TenantContext:
    """
    Decodes JWT → resolves user → injects TenantContext.
    Every protected endpoint uses this dependency so all DB queries
    are automatically scoped to the correct org_id.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TenantContext(
        user_id=user.id,
        org_id=user.org_id,
        role=user.role,
        user=user,
    )


def require_admin(ctx: TenantContext = Depends(get_tenant_ctx)) -> TenantContext:
    """Guard: admin-only endpoints."""
    if ctx.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return ctx
