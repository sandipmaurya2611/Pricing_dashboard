"""
Demand Forecasting Agent
Predicts demand elasticity, seasonal patterns, and trend impacts for individual SKUs.
"""
import json
from typing import Any, Dict
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.models import Product, DemandSignal, SignalType
from app.core.config import settings, get_llm_client

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_demand_signals",
            "description": "Get all demand signals for a product over a time period",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "period": {"type": "string", "description": "e.g. 'last_30_days', 'last_quarter'"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_seasonal_patterns",
            "description": "Get seasonal demand patterns for a product category",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["product_id"],
            },
        },
    },
]


def _exec_get_demand_signals(product_id: str, db: Session, period: str = "last_30_days") -> Dict:
    cutoff = datetime.utcnow() - timedelta(days=30)
    signals = (
        db.query(DemandSignal)
        .filter(DemandSignal.product_id == product_id, DemandSignal.captured_at >= cutoff)
        .all()
    )
    by_type = {}
    for s in signals:
        key = s.signal_type.value
        if key not in by_type:
            by_type[key] = []
        by_type[key].append({"value": s.signal_value, "period": s.period})

    # Average values per type
    avg_by_type = {k: round(sum(x["value"] for x in v) / len(v), 2) for k, v in by_type.items()}
    return {"signals_by_type": avg_by_type, "total_signals": len(signals), "period": period}


def _exec_get_seasonal_patterns(product_id: str, db: Session, category: str = "") -> Dict:
    """Return seasonal signals for context."""
    seasonal = (
        db.query(DemandSignal)
        .filter(
            DemandSignal.product_id == product_id,
            DemandSignal.signal_type == SignalType.seasonal,
        )
        .order_by(DemandSignal.captured_at.desc())
        .limit(4)
        .all()
    )
    current_month = datetime.utcnow().month
    # Simple seasonal factors by quarter
    quarter = (current_month - 1) // 3 + 1
    seasonal_factors = {1: 0.85, 2: 0.90, 3: 1.0, 4: 1.25}  # Q4 is peak for electronics
    return {
        "current_quarter": f"Q{quarter}",
        "seasonal_factor": seasonal_factors.get(quarter, 1.0),
        "historical_seasonal": [
            {"period": s.period, "value": s.signal_value} for s in seasonal
        ],
    }


async def analyze(product: Product, market_intel: Dict, db: Session) -> Dict[str, Any]:
    """Demand Forecasting Agent — predicts elasticity and demand trends."""

    system_prompt = """You are the Demand Forecasting Agent in a multi-agent pricing system.
Your job is to analyze demand signals, seasonality, and market trends to predict how price changes 
will affect unit sales and overall revenue. Use the tools to gather data, then forecast demand elasticity.
Return structured JSON with your analysis."""

    user_prompt = f"""Forecast demand for:
Product: {product.name} (SKU: {product.sku})
Current Price: ${product.current_price:.2f}
Market Intel Summary: {json.dumps(market_intel.get('data_points', {}), indent=2)}

Use tools to get demand signals and seasonal patterns. Then calculate:
1. Demand elasticity estimate (-1 to -3 scale, more negative = more elastic)
2. Velocity score (0-100, how fast is it selling)
3. Seasonal adjustment factor
4. Your confidence contribution (0-25 points)
Return as JSON."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for _ in range(4):
        client, model_name = get_llm_client()
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
                if fn_name == "get_demand_signals":
                    result = _exec_get_demand_signals(args["product_id"], db, args.get("period", "last_30_days"))
                elif fn_name == "get_seasonal_patterns":
                    result = _exec_get_seasonal_patterns(args["product_id"], db, args.get("category", ""))
                else:
                    result = {"error": "Unknown tool"}
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
        else:
            try:
                content = json.loads(msg.content) if msg.content else {}
            except Exception:
                content = {"raw": msg.content}
            return {
                "agent_name": "Demand Forecasting Agent",
                "summary": content.get("summary", "Demand analysis complete"),
                "elasticity": content.get("elasticity", -1.5),
                "velocity_score": content.get("velocity_score", 50),
                "seasonal_factor": content.get("seasonal_factor", 1.0),
                "data_points": content,
                "confidence_contribution": content.get("confidence_contribution", 25.0),
            }

    return {
        "agent_name": "Demand Forecasting Agent",
        "summary": "Demand analysis incomplete.",
        "elasticity": -1.5,
        "velocity_score": 50,
        "seasonal_factor": 1.0,
        "data_points": {},
        "confidence_contribution": 10.0,
    }
