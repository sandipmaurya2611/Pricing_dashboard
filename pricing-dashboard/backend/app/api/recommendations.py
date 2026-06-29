from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.db import get_db
from app.middleware.tenant import get_tenant_ctx, TenantContext
from app.models.models import (
    PricingRecommendation, Product, RecommendationAction, RecommendationStatus,
    ActionType
)
from app.schemas.schemas import (
    RecommendationOut, RecommendationListResponse,
    GenerateRecommendationsRequest, ApproveRequest, RejectRequest, ModifyRequest
)
from app.agents import orchestrator, execution
from app.agents.execution import execute_approved

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _enrich_rec(rec: PricingRecommendation) -> RecommendationOut:
    from app.schemas.schemas import ProductOut
    price_change_pct = round(
        ((rec.recommended_price - rec.current_price) / rec.current_price) * 100, 2
    ) if rec.current_price > 0 else 0
    out = RecommendationOut.model_validate(rec)
    out.price_change_pct = price_change_pct
    return out


@router.get("", response_model=RecommendationListResponse)
def list_recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    min_confidence: Optional[float] = None,
    product_id: Optional[str] = None,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    """List all recommendations for the org, sorted by confidence score descending."""
    query = (
        db.query(PricingRecommendation)
        .options(joinedload(PricingRecommendation.product).joinedload(Product.category))
        .filter(PricingRecommendation.org_id == ctx.org_id)
        .order_by(PricingRecommendation.confidence_score.desc(), PricingRecommendation.created_at.desc())
    )
    if status_filter:
        try:
            query = query.filter(PricingRecommendation.status == RecommendationStatus(status_filter))
        except ValueError:
            pass
    if min_confidence is not None:
        query = query.filter(PricingRecommendation.confidence_score >= min_confidence)
    if product_id:
        query = query.filter(PricingRecommendation.product_id == product_id)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return RecommendationListResponse(items=[_enrich_rec(r) for r in items], total=total)


@router.post("/generate", status_code=202)
async def generate_recommendations(
    data: GenerateRecommendationsRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    """
    Trigger the multi-agent pipeline for selected products.
    Runs agents in parallel for speed, returns recommendation IDs.
    """
    # Validate all products belong to this org
    products = db.query(Product).filter(
        Product.id.in_(data.product_ids),
        Product.org_id == ctx.org_id,
        Product.is_active == True,
    ).all()

    if not products:
        raise HTTPException(status_code=404, detail="No valid products found")

    try:
        results = await orchestrator.run_for_products(
            product_ids=[p.id for p in products],
            org_id=ctx.org_id,
            db=db,
        )
        
        # Check if any errors occurred during orchestration
        errors = [r["error"] for r in results if "error" in r]
        if errors:
            if len(errors) == len(results):
                # All failed
                raise HTTPException(status_code=500, detail=f"AI pipeline failed: {errors[0]}")
            else:
                return {
                    "message": f"Generated {len(results) - len(errors)} recommendations, {len(errors)} failed.",
                    "results": results,
                }

        return {
            "message": f"Generated {len(results)} recommendations",
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI pipeline error: {str(e)}")


@router.get("/{rec_id}", response_model=RecommendationOut)
def get_recommendation(
    rec_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    """Get a single recommendation with full agent reasoning."""
    rec = (
        db.query(PricingRecommendation)
        .options(joinedload(PricingRecommendation.product).joinedload(Product.category))
        .filter(PricingRecommendation.id == rec_id, PricingRecommendation.org_id == ctx.org_id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return _enrich_rec(rec)


@router.post("/{rec_id}/approve", status_code=200)
async def approve_recommendation(
    rec_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    rec = db.query(PricingRecommendation).filter(
        PricingRecommendation.id == rec_id, PricingRecommendation.org_id == ctx.org_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != RecommendationStatus.pending:
        raise HTTPException(status_code=400, detail=f"Cannot approve: status is '{rec.status.value}'")

    product = db.query(Product).filter(Product.id == rec.product_id).first()

    # Record the action
    action = RecommendationAction(
        recommendation_id=rec.id,
        analyst_id=ctx.user_id,
        action=ActionType.approve,
    )
    db.add(action)
    rec.status = RecommendationStatus.approved

    # Execute the price change
    exec_result = await execute_approved(
        product=product,
        recommendation=rec,
        new_price=rec.recommended_price,
        approved_by=ctx.user_id,
        db=db,
    )

    return {"message": "Approved and executed", "result": exec_result}


@router.post("/{rec_id}/reject", status_code=200)
def reject_recommendation(
    rec_id: str,
    data: RejectRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    rec = db.query(PricingRecommendation).filter(
        PricingRecommendation.id == rec_id, PricingRecommendation.org_id == ctx.org_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != RecommendationStatus.pending:
        raise HTTPException(status_code=400, detail=f"Cannot reject: status is '{rec.status.value}'")

    action = RecommendationAction(
        recommendation_id=rec.id,
        analyst_id=ctx.user_id,
        action=ActionType.reject,
        rejection_reason=data.reason,
    )
    db.add(action)
    rec.status = RecommendationStatus.rejected
    db.commit()

    return {"message": "Recommendation rejected", "reason": data.reason}


@router.post("/{rec_id}/modify", status_code=200)
async def modify_recommendation(
    rec_id: str,
    data: ModifyRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    rec = db.query(PricingRecommendation).filter(
        PricingRecommendation.id == rec_id, PricingRecommendation.org_id == ctx.org_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != RecommendationStatus.pending:
        raise HTTPException(status_code=400, detail=f"Cannot modify: status is '{rec.status.value}'")

    product = db.query(Product).filter(Product.id == rec.product_id).first()

    action = RecommendationAction(
        recommendation_id=rec.id,
        analyst_id=ctx.user_id,
        action=ActionType.modify,
        modified_price=data.new_price,
    )
    db.add(action)
    rec.status = RecommendationStatus.modified

    exec_result = await execute_approved(
        product=product,
        recommendation=rec,
        new_price=data.new_price,
        approved_by=ctx.user_id,
        db=db,
    )

    return {"message": "Modified and executed", "new_price": data.new_price, "result": exec_result}
