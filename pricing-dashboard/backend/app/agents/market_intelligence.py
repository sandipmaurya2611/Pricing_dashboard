"""
Market Intelligence Agent
Ingests competitor pricing and demand signals. Normalizes and enriches raw data
for downstream agent analysis.
"""
import json
from typing import Any, Dict, List
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.models import Product, CompetitorPrice, DemandSignal
from app.core.config import settings, get_llm_client

# Tool schemas for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_competitor_prices",
            "description": "Retrieve recent competitor prices for a product SKU",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Product ID"},
                    "days_back": {"type": "integer", "description": "How many days of history to retrieve", "default": 7},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trend_signals",
            "description": "Retrieve demand trend signals for a product",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "signal_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["trend", "seasonal", "velocity"]},
                        "description": "Which types of signals to retrieve",
                    },
                },
                "required": ["product_id"],
            },
        },
    },
]


def _exec_get_competitor_prices(product_id: str, db: Session, days_back: int = 7) -> Dict:
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    prices = (
        db.query(CompetitorPrice)
        .filter(CompetitorPrice.product_id == product_id, CompetitorPrice.captured_at >= cutoff)
        .order_by(CompetitorPrice.captured_at.desc())
        .all()
    )
    if not prices:
        return {"competitors": [], "min_price": None, "max_price": None, "avg_price": None}

    price_vals = [p.price for p in prices]
    return {
        "competitors": [
            {"name": p.competitor_name, "price": p.price, "captured_at": p.captured_at.isoformat()}
            for p in prices
        ],
        "min_price": min(price_vals),
        "max_price": max(price_vals),
        "avg_price": round(sum(price_vals) / len(price_vals), 2),
        "count": len(prices),
    }


def _exec_get_trend_signals(product_id: str, db: Session, signal_types: List[str] = None) -> Dict:
    query = db.query(DemandSignal).filter(DemandSignal.product_id == product_id)
    if signal_types:
        query = query.filter(DemandSignal.signal_type.in_(signal_types))
    signals = query.order_by(DemandSignal.captured_at.desc()).limit(10).all()
    return {
        "signals": [
            {
                "type": s.signal_type.value,
                "value": s.signal_value,
                "period": s.period,
                "notes": s.notes,
            }
            for s in signals
        ]
    }


async def analyze(product: Product, db: Session) -> Dict[str, Any]:
    """
    Market Intelligence Agent main entry point.
    Uses OpenAI function calling to decide which data to retrieve,
    then synthesizes a structured market intelligence summary.
    """
    system_prompt = """You are the Market Intelligence Agent in a pricing system.
Your job is to analyze competitor prices and demand signals for a product.
Use the available tools to gather data, then produce a concise market intelligence report.
Always call both tools to get complete data. After gathering data, return a JSON summary."""

    user_prompt = f"""Analyze market intelligence for:
Product: {product.name} (SKU: {product.sku})
Current Price: ${product.current_price:.2f}
COGS: ${product.cogs:.2f}
Product ID: {product.id}

Use the tools to gather competitor prices and trend signals, then summarize your findings."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    client, model_name = get_llm_client()

    # Agentic loop — let LLM call tools as needed
    for _ in range(5):  # max iterations
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

                if fn_name == "get_competitor_prices":
                    result = _exec_get_competitor_prices(
                        args["product_id"], db, args.get("days_back", 7)
                    )
                elif fn_name == "get_trend_signals":
                    result = _exec_get_trend_signals(
                        args["product_id"], db, args.get("signal_types")
                    )
                else:
                    result = {"error": "Unknown tool"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })
        else:
            # Final response
            try:
                content = json.loads(msg.content) if msg.content else {}
            except Exception:
                content = {"raw": msg.content}

            return {
                "agent_name": "Market Intelligence Agent",
                "summary": content.get("summary", msg.content or ""),
                "competitor_delta_pct": content.get("competitor_delta_pct", 0),
                "trend_direction": content.get("trend_direction", "neutral"),
                "risk_level": content.get("risk_level", "medium"),
                "data_points": content,
                "confidence_contribution": content.get("confidence_contribution", 25.0),
            }

    return {
        "agent_name": "Market Intelligence Agent",
        "summary": "Could not complete analysis within iteration limit.",
        "competitor_delta_pct": 0,
        "trend_direction": "neutral",
        "risk_level": "medium",
        "data_points": {},
        "confidence_contribution": 10.0,
    }
