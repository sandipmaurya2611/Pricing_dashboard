from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# ──────────────────────────────────────────────────────
# Auth Schemas
# ──────────────────────────────────────────────────────

class OrgCreate(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserJoin(BaseModel):
    invite_code: str
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    org_id: str
    email: str
    full_name: Optional[str]
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────
# Product Schemas
# ──────────────────────────────────────────────────────

class CategoryOut(BaseModel):
    id: str
    name: str
    margin_floor_pct: float

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str]
    current_price: float = Field(..., gt=0)
    cogs: float = Field(..., gt=0)
    stock_qty: int = Field(0, ge=0)
    reorder_point: int = Field(10, ge=0)
    category_id: Optional[str]


class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    current_price: Optional[float] = Field(None, gt=0)
    cogs: Optional[float] = Field(None, gt=0)
    stock_qty: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    category_id: Optional[str]
    is_active: Optional[bool]


class ProductOut(BaseModel):
    id: str
    org_id: str
    sku: str
    name: str
    description: Optional[str]
    current_price: float
    cogs: float
    stock_qty: int
    reorder_point: int
    is_active: bool
    category: Optional[CategoryOut]
    created_at: datetime
    updated_at: datetime

    # Computed at query time
    margin_pct: Optional[float] = None
    recommendation_status: Optional[str] = None
    latest_competitor_price: Optional[float] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    page_size: int


# ──────────────────────────────────────────────────────
# Recommendation Schemas
# ──────────────────────────────────────────────────────

class AgentOutput(BaseModel):
    agent_name: str
    summary: str
    data_points: Dict[str, Any]
    confidence_contribution: float


class RecommendationOut(BaseModel):
    id: str
    org_id: str
    product_id: str
    product: Optional[ProductOut]
    recommended_price: float
    current_price: float
    confidence_score: float
    price_change_pct: float = 0.0
    status: str
    reasoning: Optional[Dict[str, Any]]
    agent_outputs: Optional[List[Dict[str, Any]]]
    data_sources: Optional[List[Dict[str, Any]]]
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationListResponse(BaseModel):
    items: List[RecommendationOut]
    total: int


class GenerateRecommendationsRequest(BaseModel):
    product_ids: List[str] = Field(..., min_length=1)


class ApproveRequest(BaseModel):
    pass


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=5)


class ModifyRequest(BaseModel):
    new_price: float = Field(..., gt=0)


# ──────────────────────────────────────────────────────
# Audit Schemas
# ──────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: str
    org_id: str
    product_id: str
    product: Optional[ProductOut]
    recommendation_id: Optional[str]
    previous_price: float
    new_price: float
    change_pct: float
    executed_by: Optional[str]
    approved_by: Optional[str]
    ai_recommended_price: Optional[float]
    confidence_score: Optional[float]
    execution_status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    items: List[AuditLogOut]
    total: int


# ──────────────────────────────────────────────────────
# Config Schemas
# ──────────────────────────────────────────────────────

class OrgConfigOut(BaseModel):
    id: str
    org_id: str
    auto_execute_threshold: float
    margin_floor_default: float
    escalation_rules: Optional[Dict]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrgConfigUpdate(BaseModel):
    auto_execute_threshold: Optional[float] = Field(None, ge=0, le=100)
    margin_floor_default: Optional[float] = Field(None, ge=0, le=100)
    escalation_rules: Optional[Dict]


class CategoryCreate(BaseModel):
    name: str
    margin_floor_pct: float = Field(15.0, ge=0, le=100)


# Update forward reference
TokenResponse.model_rebuild()
