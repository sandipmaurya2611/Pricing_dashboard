"""
Seed script — generates realistic data for demo:
- 1 organization + 1 admin + 1 analyst
- 5 categories with 10 products each (50 total)
- Competitor prices (5 competitors, 30-day history per product)
- Demand signals (trend, seasonal, velocity per product)
"""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal, engine
from app.models.models import Base
from app.models import Organization, User, OrgConfig, Category, Product, CompetitorPrice, DemandSignal, SignalType, UserRole
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

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
        ("Vitamix Ascent A3500", 549.99, 210.00, 25, "HB-006"),
        ("Philips Norelco Shaver 9000", 299.99, 105.00, 80, "HB-007"),
        ("Laneige Lip Sleeping Mask", 24.00, 7.00, 650, "HB-008"),
        ("NuFace Trinity Facial Device", 339.99, 125.00, 45, "HB-009"),
        ("Peloton Tread", 2695.00, 1350.00, 8, "HB-010"),
    ],
}

COMPETITORS = ["Amazon", "Walmart", "Target", "BestBuy", "Costco"]


def random_walk(base: float, days: int, volatility: float = 0.03) -> list:
    """Generate realistic price history with random walk."""
    prices = [base]
    for _ in range(days - 1):
        change = random.gauss(0, volatility)
        new_price = max(prices[-1] * (1 + change), base * 0.7)
        prices.append(round(new_price, 2))
    return prices


def seed():
    db = SessionLocal()
    try:
        print("🌱 Starting database seed...")

        # Clean existing data (for re-runs)
        for model in [DemandSignal, CompetitorPrice, Product, Category, OrgConfig, User, Organization]:
            db.query(model).delete()
        db.commit()

        # Organization
        org = Organization(name="Klypup Demo Store", slug="klypup-demo")
        db.add(org)
        db.flush()

        # Org Config
        config = OrgConfig(org_id=org.id, auto_execute_threshold=85.0, margin_floor_default=15.0)
        db.add(config)

        # Admin user
        admin = User(
            org_id=org.id,
            email="admin@klypup.com",
            password_hash=hash_password("Admin@123"),
            full_name="Alex Admin",
            role=UserRole.admin,
        )
        db.add(admin)

        # Analyst user
        analyst = User(
            org_id=org.id,
            email="analyst@klypup.com",
            password_hash=hash_password("Analyst@123"),
            full_name="Sarah Analyst",
            role=UserRole.analyst,
        )
        db.add(analyst)
        db.flush()

        # Categories
        cat_map = {}
        for cat_data in CATEGORIES:
            cat = Category(org_id=org.id, **cat_data)
            db.add(cat)
            db.flush()
            cat_map[cat_data["name"]] = cat

        # Products + Market Data
        total_products = 0
        for cat_name, products_data in PRODUCTS_BY_CATEGORY.items():
            cat = cat_map[cat_name]
            for name, price, cogs, stock, sku in products_data:
                product = Product(
                    org_id=org.id,
                    category_id=cat.id,
                    sku=sku,
                    name=name,
                    current_price=price,
                    cogs=cogs,
                    stock_qty=stock,
                    reorder_point=max(10, stock // 10),
                )
                db.add(product)
                db.flush()

                # Competitor prices — 30 days of history, 5 competitors
                for competitor in COMPETITORS:
                    # Each competitor has its own price variation
                    comp_base = price * random.uniform(0.88, 1.12)
                    history = random_walk(comp_base, 30, volatility=0.025)
                    for i, comp_price in enumerate(history):
                        captured = datetime.utcnow() - timedelta(days=29 - i)
                        cp = CompetitorPrice(
                            product_id=product.id,
                            competitor_name=competitor,
                            price=round(comp_price, 2),
                            captured_at=captured,
                        )
                        db.add(cp)

                # Demand signals
                # Trend signal (0-100)
                trend_val = random.uniform(20, 90)
                db.add(DemandSignal(
                    product_id=product.id,
                    signal_type=SignalType.trend,
                    signal_value=round(trend_val, 1),
                    period="last_30_days",
                    notes="Simulated trend score",
                ))

                # Seasonal signal (based on category)
                seasonal_factors = {"Electronics": 75, "Apparel": 60, "Sports & Outdoors": 65, "Home & Garden": 50, "Health & Beauty": 55}
                seasonal_val = seasonal_factors.get(cat_name, 60) + random.uniform(-10, 15)
                db.add(DemandSignal(
                    product_id=product.id,
                    signal_type=SignalType.seasonal,
                    signal_value=round(seasonal_val, 1),
                    period="2024-Q2",
                    notes=f"{cat_name} seasonal pattern",
                ))

                # Velocity signal (units sold per day)
                velocity = random.uniform(0.5, min(50, stock / 5))
                db.add(DemandSignal(
                    product_id=product.id,
                    signal_type=SignalType.velocity,
                    signal_value=round(velocity, 2),
                    period="last_7_days",
                    notes="Average daily units sold",
                ))

                total_products += 1

        db.commit()
        print(f"✅ Seeded successfully!")
        print(f"   Organization: {org.name} (invite code: {org.invite_code})")
        print(f"   Admin: admin@klypup.com / Admin@123")
        print(f"   Analyst: analyst@klypup.com / Analyst@123")
        print(f"   Products: {total_products}")
        print(f"   Competitor price records: {total_products * 5 * 30}")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
