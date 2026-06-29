"""
Pricing Strategy Agent (Central Orchestrator)
Synthesizes inputs from all other agents and generates the final pricing
recommendation with confidence score and written rationale.
"""
import json
from typing import Any, Dict
from openai import AsyncOpenAI

from app.models.models import Product
from app.core.config import settings, get_llm_client


async def synthesize(
    product: Product,
    market_intel: Dict,
    demand_forecast: Dict,
    inventory_cost: Dict,
) -> Dict[str, Any]:
    """
    Pricing Strategy Agent — synthesizes all agent outputs into a final recommendation.
    Uses OpenAI with strict JSON structured output.
    """

    system_prompt = """You are the Pricing Strategy Agent, the central orchestrator in a multi-agent pricing system.
You receive analysis from three specialized agents (Market Intelligence, Demand Forecasting, Inventory & Cost)
and must synthesize their findings into a single, optimal pricing recommendation.

Your output MUST be valid JSON with exactly this structure:
{
  "recommended_price": <float>,
  "confidence_score": <float 0-100>,
  "rationale": "<2-3 sentence explanation>",
  "price_change_pct": <float, negative means decrease>,
  "expected_revenue_impact": "<brief description>",
  "risk_factors": ["<risk1>", "<risk2>"],
  "data_sources": [
    {"source": "<source name>", "type": "<competitor|demand|inventory|market>", "weight": <float 0-1>}
  ],
  "agent_summaries": {
    "market_intel_weight": <float 0-1>,
    "demand_weight": <float 0-1>,
    "inventory_weight": <float 0-1>
  }
}

Rules:
- NEVER recommend below min_acceptable_price from Inventory Agent
- Consider demand elasticity: elastic products should drop less aggressively
- Overstock → bias toward discount; Critically low → bias toward premium
- Confidence reflects how much data agrees across agents"""

    user_prompt = f"""Synthesize a pricing recommendation for:

Product: {product.name} (SKU: {product.sku})
Current Price: ${product.current_price:.2f}
COGS: ${product.cogs:.2f}

=== Market Intelligence Agent Output ===
{json.dumps(market_intel, indent=2)}

=== Demand Forecasting Agent Output ===
{json.dumps(demand_forecast, indent=2)}

=== Inventory & Cost Agent Output ===
{json.dumps(inventory_cost, indent=2)}

Hard constraint: Minimum acceptable price = ${inventory_cost.get('min_acceptable_price', product.cogs * 1.15):.2f}

Generate the optimal price recommendation as JSON."""

    client, model_name = get_llm_client()

    response = await client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,  # Lower temp for more consistent pricing decisions
    )

    try:
        content = json.loads(response.choices[0].message.content)
    except Exception:
        # Fallback: no change recommendation
        content = {
            "recommended_price": product.current_price,
            "confidence_score": 40.0,
            "rationale": "Could not synthesize recommendation. Maintaining current price as safe default.",
            "price_change_pct": 0.0,
            "expected_revenue_impact": "No change",
            "risk_factors": ["LLM synthesis failed"],
            "data_sources": [],
            "agent_summaries": {},
        }

    # Safety: enforce hard price floor
    min_price = inventory_cost.get("min_acceptable_price", product.cogs * 1.10)
    recommended = content.get("recommended_price", product.current_price)
    if recommended < min_price:
        recommended = min_price
        content["recommended_price"] = recommended
        content["confidence_score"] = max(content.get("confidence_score", 50) - 15, 20)
        content["rationale"] = f"[FLOOR ENFORCED] {content.get('rationale', '')} Price adjusted to margin floor."

    return {
        "agent_name": "Pricing Strategy Agent",
        "recommended_price": round(recommended, 2),
        "confidence_score": round(min(max(content.get("confidence_score", 50), 0), 100), 1),
        "rationale": content.get("rationale", ""),
        "price_change_pct": round(
            ((recommended - product.current_price) / product.current_price) * 100, 2
        ),
        "expected_revenue_impact": content.get("expected_revenue_impact", ""),
        "risk_factors": content.get("risk_factors", []),
        "data_sources": content.get("data_sources", []),
        "agent_summaries": content.get("agent_summaries", {}),
        "full_output": content,
    }
