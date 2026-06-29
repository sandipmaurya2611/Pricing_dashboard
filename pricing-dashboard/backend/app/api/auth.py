import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db import get_db
from app.models.models import Organization, User, OrgConfig, UserRole
from app.schemas.schemas import OrgCreate, UserLogin, UserJoin, TokenResponse, UserOut
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(data: OrgCreate, db: Session = Depends(get_db)):
    """Create a new organization and its first admin user."""
    # Check slug uniqueness
    if db.query(Organization).filter(Organization.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="Organization slug already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organization(name=data.org_name, slug=data.slug)
    db.add(org)
    db.flush()

    # Default org config
    config = OrgConfig(org_id=org.id)
    db.add(config)

    user = User(
        org_id=org.id,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "org_id": org.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login with email + password. Returns JWT."""
    user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id, "org_id": user.org_id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.post("/join", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def join_org(data: UserJoin, db: Session = Depends(get_db)):
    """Join an existing org via invite code."""
    org = db.query(Organization).filter(Organization.invite_code == data.invite_code.upper()).first()
    if not org:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        org_id=org.id,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.analyst,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "org_id": org.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def get_me(
    db: Session = Depends(get_db),
    ctx=Depends(__import__("app.middleware.tenant", fromlist=["get_tenant_ctx"]).get_tenant_ctx),
):
    """Return current authenticated user info."""
    return UserOut.model_validate(ctx.user)
