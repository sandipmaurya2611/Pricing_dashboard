"""
Agent Orchestrator
Autonomous LLM loop that orchestrates Market Intelligence, Demand Forecasting, and Inventory agents.
It decides dynamically which agents to invoke as tools before making a final decision.
"""
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from app.models.models import Product, PricingRecommendation, RecommendationStatus
from app.agents import market_intelligence, demand_forecast, inventory_cost, pricing_strategy, execution
from app.core.config import settings, get_llm_client


async def run_for_products(
    product_ids: List[str],
    org_id: str,
    db: Session,
) -> List[Dict[str, Any]]:
    """
    Run the autonomous orchestrator for a list of products.
    """
    results = []
    for product_id in product_ids:
        product = db.query(Product).filter(
            Product.id == product_id, Product.org_id == org_id
        ).first()
        if not product:
            results.append({"product_id": product_id, "error": "Product not found"})
            continue

        try:
            result = await _run_autonomous_pipeline(product, org_id, db)
            results.append(result)
        except Exception as e:
            results.append({"product_id": product_id, "error": str(e)})

        # Give Groq a 3-second breathing room between processing products
        await asyncio.sleep(3)

    return results


async def _run_autonomous_pipeline(product: Product, org_id: str, db: Session) -> Dict[str, Any]:
    """
    Autonomous Orchestrator using OpenAI Tool Calling.
    It receives the product context and decides which sub-agents to invoke.
    """
    has_groq = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip() != "")
    
    if not has_groq:
        # Mock mode if user hasn't provided a Groq API key
        return await _run_mock_pipeline(product, org_id, db)

    system_prompt = """You are the Chief Pricing Orchestrator. 
Your goal is to formulate a pricing strategy for a specific product.
You have three specialized agent tools at your disposal:
1. `analyze_market`: Gathers competitor pricing and trend signals.
2. `analyze_inventory`: Checks stock levels and calculates hard margin floors.
3. `analyze_demand`: Forecasts demand elasticity (Requires market data first).

RULES:
- You must gather sufficient data using these tools before finalizing a price.
- You must always check inventory constraints to avoid selling below margin floors.
- When you have enough data, use the `finalize_pricing_strategy` tool to submit the final decision. DO NOT output text, only call the finalize tool."""

    user_prompt = f"""Formulate a pricing strategy for:
Product: {product.name} (SKU: {product.sku})
Current Price: ${product.current_price:.2f}
COGS: ${product.cogs:.2f}

Begin your analysis."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "analyze_market",
                "description": "Call the Market Intelligence agent to get competitor prices and trends.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_inventory",
                "description": "Call the Inventory agent to get stock status and min margin floors.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_demand",
                "description": "Call the Demand Forecast agent. Pass the market data you received from analyze_market.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "market_data_summary": {"type": "string", "description": "Brief summary of market intelligence"}
                    },
                    "required": ["market_data_summary"]
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "finalize_pricing_strategy",
                "description": "Submit the final pricing recommendation. Call this ONLY when you have gathered all necessary data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recommended_price": {"type": "number"},
                        "confidence_score": {"type": "number", "description": "0-100"},
                        "rationale": {"type": "string", "description": "2-3 sentences"},
                        "price_change_pct": {"type": "number"},
                        "expected_revenue_impact": {"type": "string"},
                        "risk_factors": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["recommended_price", "confidence_score", "rationale", "price_change_pct", "expected_revenue_impact", "risk_factors"]
                },
            },
        }
    ]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    market_out = {}
    inventory_out = {}
    demand_out = {}
    final_strategy = None
    
    client, model_name = get_llm_client()

    for _ in range(8):  # Allow up to 8 agentic reasoning steps
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                
                if fn_name == "analyze_market":
                    market_out = await market_intelligence.analyze(product, db)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(market_out)})
                
                elif fn_name == "analyze_inventory":
                    inventory_out = await inventory_cost.analyze(product, org_id, db)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(inventory_out)})
                
                elif fn_name == "analyze_demand":
                    args = json.loads(tc.function.arguments)
                    # We pass the real market_out object under the hood even if the LLM passed a summary string
                    demand_out = await demand_forecast.analyze(product, market_out, db)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(demand_out)})
                
                elif fn_name == "finalize_pricing_strategy":
                    final_strategy = json.loads(tc.function.arguments)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": "{\"status\": \"success\"}"})
                    break # We have the final answer
                else:
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": "{\"error\": \"Unknown tool\"}"})
            
            if final_strategy:
                break
        else:
            messages.append({"role": "assistant", "content": msg.content})

    # Fallback if the LLM loop failed to call finalize_pricing_strategy
    if not final_strategy:
        final_strategy = {
            "recommended_price": product.current_price,
            "confidence_score": 30.0,
            "rationale": "Autonomous orchestration loop failed to synthesize data. Defaulting to current price.",
            "price_change_pct": 0.0,
            "expected_revenue_impact": "Neutral",
            "risk_factors": ["LLM orchestration timeout"]
        }

    # Ensure hard constraints (Margin floor)
    min_price = inventory_out.get("min_acceptable_price", product.cogs * 1.15)
    recommended = final_strategy.get("recommended_price", product.current_price)
    if recommended < min_price:
        recommended = min_price
        final_strategy["recommended_price"] = recommended
        final_strategy["rationale"] = f"[FLOOR ENFORCED] {final_strategy.get('rationale', '')} Price raised to meet margin requirements."
        final_strategy["confidence_score"] = max(final_strategy.get("confidence_score", 50) - 20, 20)

    # Save Recommendation
    recommendation = PricingRecommendation(
        org_id=org_id,
        product_id=product.id,
        recommended_price=recommended,
        current_price=product.current_price,
        confidence_score=final_strategy["confidence_score"],
        status=RecommendationStatus.pending,
        reasoning={
            "rationale": final_strategy["rationale"],
            "price_change_pct": final_strategy.get("price_change_pct", 0),
            "expected_revenue_impact": final_strategy.get("expected_revenue_impact", ""),
            "risk_factors": final_strategy.get("risk_factors", []),
        },
        agent_outputs=[market_out, demand_out, inventory_out],
        data_sources=[],
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(recommendation)
    db.flush()

    # Execute Compliance Agent
    exec_result = await execution.process(
        product=product,
        strategy_output={**final_strategy, "min_acceptable_price_enforced": min_price},
        org_id=org_id,
        db=db,
        recommendation=recommendation,
    )

    db.commit()
    db.refresh(recommendation)

    return {
        "product_id": product.id,
        "product_name": product.name,
        "recommendation_id": recommendation.id,
        "current_price": product.current_price,
        "recommended_price": recommendation.recommended_price,
        "confidence_score": recommendation.confidence_score,
        "status": recommendation.status.value,
        "execution_result": exec_result,
        "agents_ran": ["Autonomous Orchestrator", "Market Intelligence", "Inventory & Cost", "Demand Forecasting", "Execution & Compliance"],
    }


async def _run_mock_pipeline(product: Product, org_id: str, db: Session) -> Dict[str, Any]:
    import random
    
    # 1. Mock Market Intel
    market_out = {
        "agent_name": "Market Intelligence Agent (Mock)",
        "summary": "Competitor prices are trending lower. Amazon recently dropped prices by 5%.",
        "competitor_delta_pct": -5.0,
        "trend_direction": "down",
        "risk_level": "medium",
        "data_points": {"avg_competitor_price": product.current_price * 0.95},
        "confidence_contribution": 25.0
    }
    
    # 2. Mock Inventory Cost
    min_price = product.cogs * 1.15
    inventory_out = {
        "agent_name": "Inventory & Cost Agent (Mock)",
        "summary": "Stock levels are normal. Margin floor is 15%.",
        "inventory_flag": "normal",
        "min_acceptable_price": min_price,
        "pricing_direction_bias": "neutral",
        "hard_constraint_met": True,
        "data_points": {"cogs": product.cogs},
        "confidence_contribution": 25.0
    }
    
    # 3. Mock Demand
    demand_out = {
        "agent_name": "Demand Forecasting Agent (Mock)",
        "summary": "Demand is stable. Seasonal uptick expected next month.",
        "forecast_velocity": 5.0,
        "price_elasticity": 1.2,
        "demand_trend": "stable",
        "confidence_contribution": 25.0
    }
    
    # Calculate mock price
    recommended = round(product.current_price * random.uniform(0.92, 1.05), 2)
    if recommended < min_price:
        recommended = min_price
        
    change_pct = round(((recommended - product.current_price) / product.current_price) * 100, 2)
    
    recommendation = PricingRecommendation(
        org_id=org_id,
        product_id=product.id,
        recommended_price=recommended,
        current_price=product.current_price,
        confidence_score=85.0,
        status=RecommendationStatus.pending,
        reasoning={
            "rationale": "[MOCK MODE - No API Key] The AI has evaluated competitor drops (-5%) and stable demand. It recommends a price adjustment while strictly adhering to the 15% margin floor.",
            "price_change_pct": change_pct,
            "expected_revenue_impact": "Slight increase due to matching competitor volume.",
            "risk_factors": ["Competitor retaliation", "Mock data variance"],
        },
        agent_outputs=[market_out, demand_out, inventory_out],
        data_sources=[],
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(recommendation)
    db.flush()

    exec_result = await execution.process(
        product=product,
        strategy_output={
            "recommended_price": recommended,
            "price_change_pct": change_pct,
            "min_acceptable_price_enforced": min_price
        },
        org_id=org_id,
        db=db,
        recommendation=recommendation,
    )

    db.commit()
    db.refresh(recommendation)

    return {
        "product_id": product.id,
        "product_name": product.name,
        "recommendation_id": recommendation.id,
        "current_price": product.current_price,
        "recommended_price": recommendation.recommended_price,
        "confidence_score": recommendation.confidence_score,
        "status": recommendation.status.value,
        "execution_result": exec_result,
        "agents_ran": ["Autonomous Orchestrator (Mock)"],
    }
