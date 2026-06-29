import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Float, Integer, ForeignKey,
    DateTime, Text, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base
import enum


def gen_uuid():
    return str(uuid.uuid4())


# ──────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"


class RecommendationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    auto_executed = "auto_executed"
    modified = "modified"


class ActionType(str, enum.Enum):
    approve = "approve"
    reject = "reject"
    modify = "modify"


class ExecutionStatus(str, enum.Enum):
    success = "success"
    failed = "failed"
    rolled_back = "rolled_back"


class SignalType(str, enum.Enum):
    trend = "trend"
    seasonal = "seasonal"
    velocity = "velocity"


# ──────────────────────────────────────────────────────
# Organizations & Users
# ──────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    invite_code = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:8].upper())
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="org")
    products = relationship("Product", back_populates="org")
    org_config = relationship("OrgConfig", back_populates="org", uselist=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SAEnum(UserRole), default=UserRole.analyst, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    org = relationship("Organization", back_populates="users")


class OrgConfig(Base):
    __tablename__ = "org_configs"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), unique=True, nullable=False)
    auto_execute_threshold = Column(Float, default=85.0)   # confidence % above which auto-execute
    margin_floor_default = Column(Float, default=15.0)     # minimum margin % for any product
    escalation_rules = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    org = relationship("Organization", back_populates="org_config")


# ──────────────────────────────────────────────────────
# Product Catalog
# ──────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    margin_floor_pct = Column(Float, default=15.0)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    sku = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    current_price = Column(Float, nullable=False)
    cogs = Column(Float, nullable=False)           # cost of goods sold
    stock_qty = Column(Integer, default=0)
    reorder_point = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    org = relationship("Organization", back_populates="products")
    category = relationship("Category", back_populates="products")
    competitor_prices = relationship("CompetitorPrice", back_populates="product")
    demand_signals = relationship("DemandSignal", back_populates="product")
    recommendations = relationship("PricingRecommendation", back_populates="product")
    audit_logs = relationship("AuditLog", back_populates="product")


# ──────────────────────────────────────────────────────
# Market Data
# ──────────────────────────────────────────────────────

class CompetitorPrice(Base):
    __tablename__ = "competitor_prices"

    id = Column(String, primary_key=True, default=gen_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    competitor_name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    url = Column(String(500))
    captured_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="competitor_prices")


class DemandSignal(Base):
    __tablename__ = "demand_signals"

    id = Column(String, primary_key=True, default=gen_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    signal_type = Column(SAEnum(SignalType), nullable=False)
    signal_value = Column(Float, nullable=False)     # 0–100 normalized
    period = Column(String(50))                       # e.g. "2024-Q4", "2024-06"
    notes = Column(Text)
    captured_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="demand_signals")


# ──────────────────────────────────────────────────────
# AI Recommendations
# ──────────────────────────────────────────────────────

class PricingRecommendation(Base):
    __tablename__ = "pricing_recommendations"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)

    recommended_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)   # 0–100

    status = Column(SAEnum(RecommendationStatus), default=RecommendationStatus.pending)

    # AI reasoning stored as JSON
    reasoning = Column(JSON)           # Final rationale string
    agent_outputs = Column(JSON)       # Per-agent contributions
    data_sources = Column(JSON)        # Source attribution

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    product = relationship("Product", back_populates="recommendations")
    actions = relationship("RecommendationAction", back_populates="recommendation")
    audit_logs = relationship("AuditLog", back_populates="recommendation")


class RecommendationAction(Base):
    __tablename__ = "recommendation_actions"

    id = Column(String, primary_key=True, default=gen_uuid)
    recommendation_id = Column(String, ForeignKey("pricing_recommendations.id"), nullable=False)
    analyst_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(SAEnum(ActionType), nullable=False)
    modified_price = Column(Float)        # Only for "modify" action
    rejection_reason = Column(Text)       # Only for "reject" action
    acted_at = Column(DateTime, default=datetime.utcnow)

    recommendation = relationship("PricingRecommendation", back_populates="actions")
    analyst = relationship("User")


# ──────────────────────────────────────────────────────
# Audit Trail
# ──────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    recommendation_id = Column(String, ForeignKey("pricing_recommendations.id"))

    previous_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    change_pct = Column(Float, nullable=False)

    executed_by = Column(String)          # user_id or "auto"
    approved_by = Column(String, ForeignKey("users.id"))

    ai_recommended_price = Column(Float)
    confidence_score = Column(Float)

    execution_status = Column(SAEnum(ExecutionStatus), default=ExecutionStatus.success)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="audit_logs")
    recommendation = relationship("PricingRecommendation", back_populates="audit_logs")
    approver = relationship("User", foreign_keys=[approved_by])
