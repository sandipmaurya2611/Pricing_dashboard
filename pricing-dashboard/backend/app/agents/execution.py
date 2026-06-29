"""
Execution & Compliance Agent
Validates recommendations against business rules.
Executes approved changes or routes to human reviewers.
Handles rollback on failure.
"""
import json
import random
import httpx
from typing import Any, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import (
    Product, PricingRecommendation, RecommendationStatus,
    AuditLog, ExecutionStatus, OrgConfig
)
from app.core.config import settings


MOCK_ECOMMERCE_URL = "http://localhost:8000/mock-ecommerce/update-price"


async def process(
    product: Product,
    strategy_output: Dict,
    org_id: str,
    db: Session,
    recommendation: PricingRecommendation,
    executed_by: str = "auto",
) -> Dict[str, Any]:
    """
    Execution Agent:
    1. Validates against org config thresholds
    2. Determines if auto-execute or human-review
    3. Executes if auto-execute
    4. Records audit log in all cases
    """
    org_config = db.query(OrgConfig).filter(OrgConfig.org_id == org_id).first()
    auto_threshold = org_config.auto_execute_threshold if org_config else 85.0

    confidence = strategy_output.get("confidence_score", 0)
    recommended_price = strategy_output.get("recommended_price", product.current_price)
    min_price = strategy_output.get("min_acceptable_price_enforced", recommended_price)

    # Compliance check: margin floor
    if recommended_price < (product.cogs * 1.05):
        return {
            "action": "rejected_compliance",
            "reason": "Price below minimum acceptable threshold (5% above COGS)",
            "executed": False,
        }

    # Route based on confidence
    if confidence >= auto_threshold:
        # Auto-execute path
        result = await _call_mock_ecommerce(product.id, product.sku, recommended_price)

        if result["success"]:
            # Update product price in DB
            old_price = product.current_price
            product.current_price = recommended_price
            product.updated_at = datetime.utcnow()
            recommendation.status = RecommendationStatus.auto_executed

            # Audit log
            _record_audit(
                db=db,
                org_id=org_id,
                product=product,
                recommendation=recommendation,
                old_price=old_price,
                new_price=recommended_price,
                executed_by="auto",
                status=ExecutionStatus.success,
            )
            db.commit()

            return {
                "action": "auto_executed",
                "old_price": old_price,
                "new_price": recommended_price,
                "confidence": confidence,
                "executed": True,
                "message": f"Auto-executed: price changed ${old_price:.2f} → ${recommended_price:.2f}",
            }
        else:
            # Rollback — price remains unchanged, log failure
            recommendation.status = RecommendationStatus.pending
            _record_audit(
                db=db,
                org_id=org_id,
                product=product,
                recommendation=recommendation,
                old_price=product.current_price,
                new_price=recommended_price,
                executed_by="auto",
                status=ExecutionStatus.failed,
                error_message=result.get("error", "Unknown error"),
            )
            db.commit()

            return {
                "action": "auto_execute_failed",
                "reason": result.get("error"),
                "executed": False,
                "fallback": "Routed to human review",
            }
    else:
        # Route to human review
        recommendation.status = RecommendationStatus.pending
        db.commit()

        return {
            "action": "routed_to_review",
            "confidence": confidence,
            "threshold": auto_threshold,
            "executed": False,
            "message": f"Confidence {confidence:.1f}% < threshold {auto_threshold:.1f}%. Awaiting analyst approval.",
        }


async def execute_approved(
    product: Product,
    recommendation: PricingRecommendation,
    new_price: float,
    approved_by: str,
    db: Session,
) -> Dict[str, Any]:
    """Called when analyst manually approves/modifies a recommendation."""
    result = await _call_mock_ecommerce(product.id, product.sku, new_price)

    old_price = product.current_price

    if result["success"]:
        product.current_price = new_price
        product.updated_at = datetime.utcnow()

        _record_audit(
            db=db,
            org_id=product.org_id,
            product=product,
            recommendation=recommendation,
            old_price=old_price,
            new_price=new_price,
            executed_by=approved_by,
            approved_by=approved_by,
            status=ExecutionStatus.success,
        )
        db.commit()
        return {"success": True, "old_price": old_price, "new_price": new_price}
    else:
        _record_audit(
            db=db,
            org_id=product.org_id,
            product=product,
            recommendation=recommendation,
            old_price=old_price,
            new_price=new_price,
            executed_by=approved_by,
            approved_by=approved_by,
            status=ExecutionStatus.failed,
            error_message=result.get("error"),
        )
        db.commit()
        return {"success": False, "error": result.get("error")}


async def _call_mock_ecommerce(product_id: str, sku: str, new_price: float) -> Dict:
    """
    Mock e-commerce platform API call.
    Simulates 20% failure rate for realistic error handling demonstration.
    """
    # Simulate failure rate
    if random.random() < settings.MOCK_ECOMMERCE_FAILURE_RATE:
        return {"success": False, "error": "Mock e-commerce API timeout (simulated failure)"}

    # In production this would be a real HTTP call
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(MOCK_ECOMMERCE_URL, json={...})

    return {
        "success": True,
        "platform": "MockEcommerceAPI",
        "product_id": product_id,
        "sku": sku,
        "new_price": new_price,
        "executed_at": datetime.utcnow().isoformat(),
    }


def _record_audit(
    db: Session,
    org_id: str,
    product: Product,
    recommendation: PricingRecommendation,
    old_price: float,
    new_price: float,
    executed_by: str,
    approved_by: str = None,
    status: ExecutionStatus = ExecutionStatus.success,
    error_message: str = None,
):
    change_pct = round(((new_price - old_price) / old_price) * 100, 2) if old_price > 0 else 0
    log = AuditLog(
        org_id=org_id,
        product_id=product.id,
        recommendation_id=recommendation.id,
        previous_price=old_price,
        new_price=new_price,
        change_pct=change_pct,
        executed_by=executed_by,
        approved_by=approved_by,
        ai_recommended_price=recommendation.recommended_price,
        confidence_score=recommendation.confidence_score,
        execution_status=status,
        error_message=error_message,
    )
    db.add(log)
