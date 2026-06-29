"""
Inventory & Cost Agent
Monitors inventory levels, cost-of-goods, and margin thresholds.
Flags constraints to prevent margin erosion.
"""
import json
from typing import Any, Dict
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.models.models import Product, OrgConfig, Category
from app.core.config import settings, get_llm_client

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_inventory_status",
            "description": "Get current inventory status including stock levels and reorder points",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_margin_floor",
            "description": "Get the minimum acceptable margin percentage for a product category",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "org_id": {"type": "string"},
                },
                "required": ["product_id", "org_id"],
            },
        },
    },
]


def _exec_get_inventory_status(product_id: str, db: Session) -> Dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}

    stock_status = "normal"
    if product.stock_qty == 0:
        stock_status = "out_of_stock"
    elif product.stock_qty <= product.reorder_point:
        stock_status = "critically_low"
    elif product.stock_qty >= product.reorder_point * 10:
        stock_status = "overstocked"

    return {
        "product_id": product_id,
        "stock_qty": product.stock_qty,
        "reorder_point": product.reorder_point,
        "stock_status": stock_status,
        "cogs": product.cogs,
        "current_price": product.current_price,
        "current_margin_pct": round(((product.current_price - product.cogs) / product.current_price) * 100, 2),
    }


def _exec_get_margin_floor(product_id: str, org_id: str, db: Session) -> Dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    org_config = db.query(OrgConfig).filter(OrgConfig.org_id == org_id).first()

    margin_floor = org_config.margin_floor_default if org_config else 15.0

    # Category-level override
    if product and product.category_id:
        cat = db.query(Category).filter(Category.id == product.category_id).first()
        if cat:
            margin_floor = cat.margin_floor_pct

    min_price_for_margin = None
    if product:
        # min_price = cogs / (1 - margin_floor/100)
        min_price_for_margin = round(product.cogs / (1 - margin_floor / 100), 2)

    return {
        "margin_floor_pct": margin_floor,
        "min_acceptable_price": min_price_for_margin,
        "cogs": product.cogs if product else None,
    }


async def analyze(product: Product, org_id: str, db: Session) -> Dict[str, Any]:
    """Inventory & Cost Agent — flags hard constraints on pricing."""

    system_prompt = """You are the Inventory & Cost Agent in a multi-agent pricing system.
Your job is to enforce hard constraints: never recommend a price below the margin floor,
flag overstock situations that need clearance pricing, and flag low-stock situations that 
allow premium pricing. Use both tools and return structured JSON analysis."""

    user_prompt = f"""Analyze inventory and cost constraints for:
Product: {product.name} (SKU: {product.sku})
Current Price: ${product.current_price:.2f}
COGS: ${product.cogs:.2f}
Org ID: {org_id}
Product ID: {product.id}

Use tools to get inventory status and margin floor. Then determine:
1. inventory_flag: "overstock" | "critically_low" | "out_of_stock" | "normal"
2. min_acceptable_price (hard floor based on COGS + margin floor)
3. pricing_direction_bias: "increase" | "decrease" | "neutral" (based on inventory)
4. hard_constraint_met: true if recommended price is above min_acceptable_price
5. confidence_contribution (0-25 points)
Return as JSON."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    client, model_name = get_llm_client()

    for _ in range(4):
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                args = json.loads(tc.function.arguments)
                if fn_name == "get_inventory_status":
                    result = _exec_get_inventory_status(args["product_id"], db)
                elif fn_name == "get_margin_floor":
                    result = _exec_get_margin_floor(args["product_id"], args["org_id"], db)
                else:
                    result = {"error": "Unknown tool"}
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
        else:
            try:
                content = json.loads(msg.content) if msg.content else {}
            except Exception:
                content = {"raw": msg.content}
            return {
                "agent_name": "Inventory & Cost Agent",
                "summary": content.get("summary", "Inventory analysis complete"),
                "inventory_flag": content.get("inventory_flag", "normal"),
                "min_acceptable_price": content.get("min_acceptable_price", product.cogs * 1.15),
                "pricing_direction_bias": content.get("pricing_direction_bias", "neutral"),
                "hard_constraint_met": content.get("hard_constraint_met", True),
                "data_points": content,
                "confidence_contribution": content.get("confidence_contribution", 25.0),
            }

    # Fallback
    min_price = round(product.cogs / (1 - 0.15), 2)
    return {
        "agent_name": "Inventory & Cost Agent",
        "summary": "Analysis incomplete — using default constraints.",
        "inventory_flag": "normal",
        "min_acceptable_price": min_price,
        "pricing_direction_bias": "neutral",
        "hard_constraint_met": True,
        "data_points": {},
        "confidence_contribution": 10.0,
    }
