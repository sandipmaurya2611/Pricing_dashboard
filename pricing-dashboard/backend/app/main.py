from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.core.config import settings
from app.api import auth, products, recommendations, audit, config
from app.db import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Dynamic Pricing Intelligence Dashboard",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "*"}
    )


# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(config.router, prefix="/api")


# Mock E-Commerce API endpoint
@app.post("/mock-ecommerce/update-price")
async def mock_ecommerce_update(request: Request):
    """
    Simulates the external e-commerce platform price update API.
    This is what the Execution Agent calls when auto-executing price changes.
    """
    body = await request.json()
    import random
    if random.random() < settings.MOCK_ECOMMERCE_FAILURE_RATE:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Platform temporarily unavailable"},
        )
    return {
        "success": True,
        "product_id": body.get("product_id"),
        "new_price": body.get("new_price"),
        "platform": "MockEcommerceAPI v1",
        "message": "Price updated successfully on e-commerce platform",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/")
def root():
    return {"message": "Pricing Intelligence Dashboard API", "docs": "/docs"}


@app.get("/make-admin")
def make_admin(email: str, password: str, name: str = "Admin"):
    """
    Emergency endpoint: creates an admin user in the existing org.
    Use this if you've lost access to your account.
    Example: /make-admin?email=you@email.com&password=YourPass&name=Sandip
    """
    from app.db import SessionLocal
    from app.models.models import Organization, User, OrgConfig, UserRole
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        if not org:
            return {"error": "No organization found. Please sign up first."}

        # Check if email already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            # Update password instead
            existing.password_hash = hash_password(password)
            existing.full_name = name
            existing.role = UserRole.admin
            existing.is_active = True
            db.commit()
            return {"success": True, "message": f"Password updated for {email}", "org": org.name}

        # Create new admin
        user = User(
            org_id=org.id,
            email=email,
            password_hash=hash_password(password),
            full_name=name,
            role=UserRole.admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
        return {"success": True, "message": f"Admin account created: {email}", "org": org.name}
    finally:
        db.close()


@app.get("/seed-now")
def seed_now(email: str = None):
    """
    Seeds 50 demo products into the user's organization.
    Example: /seed-now?email=sandip@example.com
    Preserves all existing users and accounts — only adds/replaces product catalog data.
    """
    if not email:
        return {"error": "Please provide an email query param, e.g. /seed-now?email=sandip@example.com"}

    import random
    from datetime import datetime, timedelta
    from app.db import SessionLocal
    from app.models.models import (
        Organization, User, OrgConfig, Category, Product,
        CompetitorPrice, DemandSignal, SignalType
    )

    CATEGORIES = [
        {"name": "Electronics", "margin_floor_pct": 12.0},
        {"name": "Home & Garden", "margin_floor_pct": 20.0},
        {"name": "Apparel", "margin_floor_pct": 35.0},
        {"name": "Sports & Outdoors", "margin_floor_pct": 25.0},
        {"name": "Health & Beauty", "margin_floor_pct": 30.0},
    ]

    PRODUCTS_BY_CATEGORY = {
        "Electronics": [
            ("Sony WH-1000XM5 Headphones", 299.99, 145.00, 280, "ELEC-001"),
            ("Apple AirPods Pro", 249.99, 120.00, 150, "ELEC-002"),
            ("Samsung 65\" 4K TV", 799.99, 410.00, 45, "ELEC-003"),
            ("Logitech MX Master 3 Mouse", 99.99, 42.00, 320, "ELEC-004"),
            ("Nintendo Switch OLED", 349.99, 195.00, 90, "ELEC-005"),
            ("DJI Mini 3 Drone", 469.99, 240.00, 35, "ELEC-006"),
            ("iPad Air 5th Gen", 599.99, 310.00, 120, "ELEC-007"),
            ("Anker PowerCore 26800", 59.99, 22.00, 500, "ELEC-008"),
            ("Ring Video Doorbell Pro", 199.99, 88.00, 210, "ELEC-009"),
            ("Kindle Paperwhite", 139.99, 65.00, 380, "ELEC-010"),
        ],
        "Home & Garden": [
            ("Dyson V15 Detect Vacuum", 699.99, 320.00, 85, "HOME-001"),
            ("Instant Pot Duo 7-in-1", 89.99, 35.00, 420, "HOME-002"),
            ("Philips Hue Starter Kit", 179.99, 72.00, 165, "HOME-003"),
            ("Weber Spirit E-310 Grill", 499.99, 230.00, 30, "HOME-004"),
            ("Nest Learning Thermostat", 249.99, 95.00, 140, "HOME-005"),
            ("Keurig K-Elite Coffee Maker", 149.99, 58.00, 290, "HOME-006"),
            ("Shark Robot Vacuum", 349.99, 145.00, 95, "HOME-007"),
            ("Vitamix 5200 Blender", 449.99, 195.00, 60, "HOME-008"),
            ("Ring Alarm 5-Piece Kit", 199.99, 80.00, 175, "HOME-009"),
            ("Cuisinart Air Fryer", 119.99, 45.00, 340, "HOME-010"),
        ],
        "Apparel": [
            ("Nike Air Max 270", 149.99, 58.00, 210, "APP-001"),
            ("Levi's 501 Original Jeans", 69.99, 22.00, 380, "APP-002"),
            ("Patagonia Nano Puff Jacket", 199.99, 72.00, 90, "APP-003"),
            ("Adidas Ultraboost 22", 189.99, 68.00, 160, "APP-004"),
            ("The North Face Fleece", 129.99, 45.00, 240, "APP-005"),
            ("Ray-Ban Aviator Classic", 154.99, 52.00, 130, "APP-006"),
            ("Carhartt WIP Watch Hat", 29.99, 9.00, 580, "APP-007"),
            ("Under Armour HeatGear Shirt", 34.99, 11.00, 450, "APP-008"),
            ("Columbia Bugaboo Pants", 89.99, 30.00, 200, "APP-009"),
            ("Timberland 6-Inch Boot", 199.99, 75.00, 110, "APP-010"),
        ],
        "Sports & Outdoors": [
            ("Peloton Bike+", 2495.00, 1200.00, 15, "SPORT-001"),
            ("Hydro Flask 32oz", 49.95, 16.00, 620, "SPORT-002"),
            ("Trek FX 3 Disc Bike", 899.99, 380.00, 18, "SPORT-003"),
            ("Garmin Forerunner 255", 349.99, 155.00, 75, "SPORT-004"),
            ("Coleman 6-Person Tent", 129.99, 48.00, 95, "SPORT-005"),
            ("Osprey Atmos AG 65 Pack", 299.99, 115.00, 55, "SPORT-006"),
            ("Fitbit Charge 5", 149.99, 58.00, 190, "SPORT-007"),
            ("Yeti Tundra 45 Cooler", 324.99, 135.00, 40, "SPORT-008"),
            ("Black Diamond Headlamp", 59.99, 20.00, 280, "SPORT-009"),
            ("Callaway Strata Golf Set", 299.99, 120.00, 30, "SPORT-010"),
        ],
        "Health & Beauty": [
            ("Oral-B iO Series 9", 199.99, 65.00, 145, "HB-001"),
            ("Neutrogena Hydro Boost Serum", 24.99, 6.50, 820, "HB-002"),
            ("Theragun Pro Massager", 599.99, 225.00, 35, "HB-003"),
            ("Revlon One-Step Hair Dryer", 59.99, 18.00, 390, "HB-004"),
            ("CeraVe Moisturizing Cream", 19.99, 5.00, 1100, "HB-005"),
            ("Philips Norelco Shaver 9000", 299.99, 105.00, 80, "HB-006"),
            ("Laneige Lip Sleeping Mask", 24.00, 7.00, 650, "HB-007"),
            ("NuFace Trinity Facial Device", 339.99, 125.00, 45, "HB-008"),
            ("Garmin Instinct 2 Watch", 299.99, 130.00, 95, "HB-009"),
            ("Withings Body+ Smart Scale", 99.99, 38.00, 180, "HB-010"),
        ],
    }

    COMPETITORS = ["Amazon", "Walmart", "Target", "BestBuy", "Costco"]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"error": f"No user found with email {email}. Please use the email you log in with."}

        org = db.query(Organization).filter(Organization.id == user.org_id).first()
        
        # Ensure OrgConfig exists
        if not db.query(OrgConfig).filter(OrgConfig.org_id == org.id).first():
            db.add(OrgConfig(org_id=org.id, auto_execute_threshold=85.0, margin_floor_default=15.0))
            db.flush()

        # Wipe ONLY products/categories/signals for this org (preserving users!)
        existing_products = db.query(Product).filter(Product.org_id == org.id).all()
        for p in existing_products:
            db.query(CompetitorPrice).filter(CompetitorPrice.product_id == p.id).delete()
            db.query(DemandSignal).filter(DemandSignal.product_id == p.id).delete()
        db.query(Product).filter(Product.org_id == org.id).delete()
        db.query(Category).filter(Category.org_id == org.id).delete()
        db.flush()

        # Seed categories & products
        cat_map = {}
        for cat_data in CATEGORIES:
            cat = Category(org_id=org.id, **cat_data)
            db.add(cat)
            db.flush()
            cat_map[cat_data["name"]] = cat

        total_products = 0
        for cat_name, products_data in PRODUCTS_BY_CATEGORY.items():
            cat = cat_map[cat_name]
            for name, price, cogs, stock, sku in products_data:
                product = Product(
                    org_id=org.id, category_id=cat.id, sku=sku, name=name,
                    current_price=price, cogs=cogs, stock_qty=stock,
                    reorder_point=max(10, stock // 10),
                )
                db.add(product)
                db.flush()

                for competitor in COMPETITORS:
                    comp_base = price * random.uniform(0.88, 1.12)
                    prev = comp_base
                    for i in range(30):
                        change = random.gauss(0, 0.025)
                        prev = max(prev * (1 + change), comp_base * 0.7)
                        db.add(CompetitorPrice(
                            product_id=product.id, competitor_name=competitor,
                            price=round(prev, 2),
                            captured_at=datetime.utcnow() - timedelta(days=29 - i),
                        ))

                db.add(DemandSignal(product_id=product.id, signal_type=SignalType.trend,
                                    signal_value=round(random.uniform(20, 90), 1), period="last_30_days"))
                db.add(DemandSignal(product_id=product.id, signal_type=SignalType.seasonal,
                                    signal_value=round(random.uniform(40, 90), 1), period="2024-Q2"))
                db.add(DemandSignal(product_id=product.id, signal_type=SignalType.velocity,
                                    signal_value=round(random.uniform(0.5, min(50, stock / 5)), 2), period="last_7_days"))
                total_products += 1

        db.commit()
        
        users = db.query(User).filter(User.org_id == org.id).all()
        return {
            "success": True,
            "message": f"Seeded {total_products} products into '{org.name}' — all user accounts preserved!",
            "org": org.name,
            "preserved_users": [u.email for u in users],
            "products_added": total_products,
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


@app.post("/seed")
def seed_database():
    """One-shot seed endpoint. Clears existing data and re-seeds 50 products for the active org."""
    import random
    from datetime import datetime, timedelta
    from app.db import SessionLocal
    from app.models.models import (
        Organization, User, OrgConfig, Category, Product,
        CompetitorPrice, DemandSignal, SignalType, UserRole
    )
    from app.core.security import hash_password

    CATEGORIES = [
        {"name": "Electronics", "margin_floor_pct": 12.0},
        {"name": "Home & Garden", "margin_floor_pct": 20.0},
        {"name": "Apparel", "margin_floor_pct": 35.0},
        {"name": "Sports & Outdoors", "margin_floor_pct": 25.0},
        {"name": "Health & Beauty", "margin_floor_pct": 30.0},
    ]

    PRODUCTS_BY_CATEGORY = {
        "Electronics": [
            ("Sony WH-1000XM5 Headphones", 299.99, 145.00, 280, "ELEC-001"),
            ("Apple AirPods Pro", 249.99, 120.00, 150, "ELEC-002"),
            ("Samsung 65\" 4K TV", 799.99, 410.00, 45, "ELEC-003"),
            ("Logitech MX Master 3 Mouse", 99.99, 42.00, 320, "ELEC-004"),
            ("Nintendo Switch OLED", 349.99, 195.00, 90, "ELEC-005"),
            ("DJI Mini 3 Drone", 469.99, 240.00, 35, "ELEC-006"),
            ("iPad Air 5th Gen", 599.99, 310.00, 120, "ELEC-007"),
            ("Anker PowerCore 26800", 59.99, 22.00, 500, "ELEC-008"),
            ("Ring Video Doorbell Pro", 199.99, 88.00, 210, "ELEC-009"),
            ("Kindle Paperwhite", 139.99, 65.00, 380, "ELEC-010"),
        ],
        "Home & Garden": [
            ("Dyson V15 Detect Vacuum", 699.99, 320.00, 85, "HOME-001"),
            ("Instant Pot Duo 7-in-1", 89.99, 35.00, 420, "HOME-002"),
            ("Philips Hue Starter Kit", 179.99, 72.00, 165, "HOME-003"),
            ("Weber Spirit E-310 Grill", 499.99, 230.00, 30, "HOME-004"),
            ("Nest Learning Thermostat", 249.99, 95.00, 140, "HOME-005"),
            ("Keurig K-Elite Coffee Maker", 149.99, 58.00, 290, "HOME-006"),
            ("Shark Robot Vacuum", 349.99, 145.00, 95, "HOME-007"),
            ("Vitamix 5200 Blender", 449.99, 195.00, 60, "HOME-008"),
            ("Ring Alarm 5-Piece Kit", 199.99, 80.00, 175, "HOME-009"),
            ("Cuisinart Air Fryer", 119.99, 45.00, 340, "HOME-010"),
        ],
        "Apparel": [
            ("Nike Air Max 270", 149.99, 58.00, 210, "APP-001"),
            ("Levi's 501 Original Jeans", 69.99, 22.00, 380, "APP-002"),
            ("Patagonia Nano Puff Jacket", 199.99, 72.00, 90, "APP-003"),
            ("Adidas Ultraboost 22", 189.99, 68.00, 160, "APP-004"),
            ("The North Face Fleece", 129.99, 45.00, 240, "APP-005"),
            ("Ray-Ban Aviator Classic", 154.99, 52.00, 130, "APP-006"),
            ("Carhartt WIP Watch Hat", 29.99, 9.00, 580, "APP-007"),
            ("Under Armour HeatGear Shirt", 34.99, 11.00, 450, "APP-008"),
            ("Columbia Bugaboo Pants", 89.99, 30.00, 200, "APP-009"),
            ("Timberland 6-Inch Boot", 199.99, 75.00, 110, "APP-010"),
        ],
        "Sports & Outdoors": [
            ("Peloton Bike+", 2495.00, 1200.00, 15, "SPORT-001"),
            ("Hydro Flask 32oz", 49.95, 16.00, 620, "SPORT-002"),
            ("Trek FX 3 Disc Bike", 899.99, 380.00, 18, "SPORT-003"),
            ("Garmin Forerunner 255", 349.99, 155.00, 75, "SPORT-004"),
            ("Coleman 6-Person Tent", 129.99, 48.00, 95, "SPORT-005"),
            ("Osprey Atmos AG 65 Pack", 299.99, 115.00, 55, "SPORT-006"),
            ("Fitbit Charge 5", 149.99, 58.00, 190, "SPORT-007"),
            ("Yeti Tundra 45 Cooler", 324.99, 135.00, 40, "SPORT-008"),
            ("Black Diamond Headlamp", 59.99, 20.00, 280, "SPORT-009"),
            ("Callaway Strata Golf Set", 299.99, 120.00, 30, "SPORT-010"),
        ],
        "Health & Beauty": [
            ("Oral-B iO Series 9", 199.99, 65.00, 145, "HB-001"),
            ("Neutrogena Hydro Boost Serum", 24.99, 6.50, 820, "HB-002"),
            ("Theragun Pro Massager", 599.99, 225.00, 35, "HB-003"),
            ("Revlon One-Step Hair Dryer", 59.99, 18.00, 390, "HB-004"),
            ("CeraVe Moisturizing Cream", 19.99, 5.00, 1100, "HB-005"),
            ("Philips Norelco Shaver 9000", 299.99, 105.00, 80, "HB-006"),
            ("Laneige Lip Sleeping Mask", 24.00, 7.00, 650, "HB-007"),
            ("NuFace Trinity Facial Device", 339.99, 125.00, 45, "HB-008"),
            ("Garmin Instinct 2 Watch", 299.99, 130.00, 95, "HB-009"),
            ("Withings Body+ Smart Scale", 99.99, 38.00, 180, "HB-010"),
        ],
    }

    COMPETITORS = ["Amazon", "Walmart", "Target", "BestBuy", "Costco"]

    db = SessionLocal()
    try:
        # Wipe existing data
        for model in [DemandSignal, CompetitorPrice, Product, Category, OrgConfig, User, Organization]:
            db.query(model).delete()
        db.commit()

        org = Organization(name="Klypup Demo Store", slug="klypup-demo")
        db.add(org)
        db.flush()

        db.add(OrgConfig(org_id=org.id, auto_execute_threshold=85.0, margin_floor_default=15.0))
        db.add(User(org_id=org.id, email="admin@klypup.com", password_hash=hash_password("Admin@123"),
                    full_name="Alex Admin", role=UserRole.admin))
        db.add(User(org_id=org.id, email="analyst@klypup.com", password_hash=hash_password("Analyst@123"),
                    full_name="Sarah Analyst", role=UserRole.analyst))
        db.flush()

        cat_map = {}
        for cat_data in CATEGORIES:
            cat = Category(org_id=org.id, **cat_data)
            db.add(cat)
            db.flush()
            cat_map[cat_data["name"]] = cat

        total_products = 0
        for cat_name, products_data in PRODUCTS_BY_CATEGORY.items():
            cat = cat_map[cat_name]
            for name, price, cogs, stock, sku in products_data:
                product = Product(
                    org_id=org.id, category_id=cat.id, sku=sku, name=name,
                    current_price=price, cogs=cogs, stock_qty=stock,
                    reorder_point=max(10, stock // 10),
                )
                db.add(product)
                db.flush()

                for competitor in COMPETITORS:
                    comp_base = price * random.uniform(0.88, 1.12)
                    prev = comp_base
                    for i in range(30):
                        change = random.gauss(0, 0.025)
                        prev = max(prev * (1 + change), comp_base * 0.7)
                        db.add(CompetitorPrice(
                            product_id=product.id, competitor_name=competitor,
                            price=round(prev, 2),
                            captured_at=datetime.utcnow() - timedelta(days=29 - i),
                        ))

                db.add(DemandSignal(product_id=product.id, signal_type=SignalType.trend,
                                    signal_value=round(random.uniform(20, 90), 1), period="last_30_days"))
                db.add(DemandSignal(product_id=product.id, signal_type=SignalType.seasonal,
                                    signal_value=round(random.uniform(40, 90), 1), period="2024-Q2"))
                db.add(DemandSignal(product_id=product.id, signal_type=SignalType.velocity,
                                    signal_value=round(random.uniform(0.5, min(50, stock / 5)), 2), period="last_7_days"))
                total_products += 1

        db.commit()
        return {
            "success": True,
            "message": f"Seeded {total_products} products",
            "org": org.name,
            "invite_code": org.invite_code,
            "admin_email": "admin@klypup.com",
            "admin_password": "Admin@123",
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

