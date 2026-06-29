from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from datetime import datetime

from app.db import get_db
from app.middleware.tenant import get_tenant_ctx, require_admin, TenantContext
from app.models.models import Product, Category, PricingRecommendation, RecommendationStatus
from app.schemas.schemas import (
    ProductCreate, ProductUpdate, ProductOut, ProductListResponse,
    CategoryOut, CategoryCreate
)

router = APIRouter(prefix="/products", tags=["products"])


def _to_product_out(p: Product, db: Session) -> ProductOut:
    margin_pct = round(((p.current_price - p.cogs) / p.current_price) * 100, 2) if p.current_price > 0 else 0

    # Latest recommendation status
    latest_rec = (
        db.query(PricingRecommendation)
        .filter(PricingRecommendation.product_id == p.id)
        .order_by(PricingRecommendation.created_at.desc())
        .first()
    )

    # Latest competitor price (min across competitors)
    from app.models.models import CompetitorPrice
    latest_cp = (
        db.query(CompetitorPrice)
        .filter(CompetitorPrice.product_id == p.id)
        .order_by(CompetitorPrice.captured_at.desc())
        .first()
    )

    out = ProductOut.model_validate(p)
    out.margin_pct = margin_pct
    out.recommendation_status = latest_rec.status.value if latest_rec else None
    out.latest_competitor_price = latest_cp.price if latest_cp else None
    return out


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    """Paginated product catalog, scoped to current org."""
    query = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.org_id == ctx.org_id)
    )
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)

    total = query.count()
    products = query.offset((page - 1) * page_size).limit(page_size).all()

    # Compile the query to see exactly what is being sent to the DB
    compiled_sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

    items = [_to_product_out(p, db) for p in products]
    
    # We will temporarily print it to the terminal for the user to see, 
    # but we will also throw it in an HTTP header or similar? No, just print.
    print(f"DEBUG SQL: {compiled_sql}")
    
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(require_admin),
):
    """Create a new product (admin only)."""
    if data.category_id:
        cat = db.query(Category).filter(
            Category.id == data.category_id, Category.org_id == ctx.org_id
        ).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    product = Product(org_id=ctx.org_id, **data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return _to_product_out(product, db)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    product = db.query(Product).options(joinedload(Product.category)).filter(
        Product.id == product_id, Product.org_id == ctx.org_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_product_out(product, db)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(require_admin),
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.org_id == ctx.org_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return _to_product_out(product, db)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(require_admin),
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.org_id == ctx.org_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False  # soft delete
    db.commit()


# ── Categories ──────────────────────────────────────

@router.get("/categories/all", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
):
    return db.query(Category).filter(Category.org_id == ctx.org_id).all()


@router.post("/categories/create", response_model=CategoryOut, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(require_admin),
):
    cat = Category(org_id=ctx.org_id, **data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
@router.get("/debug-db")
def debug_db(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    names = [p.name for p in products]
    return {"total": len(names), "names": names}
