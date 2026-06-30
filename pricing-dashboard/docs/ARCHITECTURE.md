# Architecture Document — PriceIQ Pricing Intelligence Dashboard

## System Overview

PriceIQ is a multi-tenant, full-stack web application that uses a multi-agent AI system to generate dynamic pricing recommendations for e-commerce products. The architecture separates concerns cleanly across frontend, backend API, AI agent layer, and data layer.

## High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js 14)                      │
│  /login  /signup  /dashboard  /recommendations  /audit  /admin  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (Bearer JWT)
┌──────────────────────────▼──────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ API Routes: auth / products / recommendations / audit / config│
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────── Tenant Context Middleware ───────────────────┐  │
│  │ JWT decode → resolve user → inject TenantContext (org_id)  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────── Multi-Agent Pipeline ────────────────────┐  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │  │
│  │  │ Market Intel │  │ Demand Fcst  │  │Inventory&Cost  │   │  │
│  │  │    Agent     │  │    Agent     │  │    Agent       │   │  │
│  │  │  (dynamic)   │  │ (dynamic)    │  │  (dynamic)     │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘   │  │
│  │         └─────────────────▼───────────────────┘           │  │
│  │                   Pricing Strategy Agent                   │  │
│  │              (GPT-4o, JSON structured output)              │  │
│  │                           │                                │  │
│  │               Execution & Compliance Agent                 │  │
│  │      (auto-execute if confidence ≥ threshold | queue)      │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     PostgreSQL Database                          │
│                                                                  │
│  organizations, users, org_configs                               │
│  categories, products                                            │
│  competitor_prices, demand_signals                               │
│  pricing_recommendations, recommendation_actions                 │
│  audit_logs                                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Multi-Tenant Design

All tenant-scoped tables include an `org_id` column (FK → organizations).

A FastAPI dependency (`get_tenant_ctx`) runs on every protected request:
1. Decodes JWT → extracts `user_id`
2. Loads `User` from DB → gets `org_id`
3. Injects `TenantContext(user_id, org_id, role)` into the route handler
4. All DB queries filter `.filter(Model.org_id == ctx.org_id)`

This ensures **no cross-tenant data leakage** at the ORM layer.

## Multi-Agent Design

### Agent Communication Pattern
We utilize an **Autonomous Orchestrator Loop** using OpenAI/Groq Tool Calling. 
Instead of hardcoding a sequence, the Strategy LLM is given access to 3 distinct sub-agent tools:
1. `analyze_market`
2. `analyze_inventory`
3. `analyze_demand`

The Orchestrator dictates which tools to call and synthesizes the final output dynamically.

### Structured Output
The Pricing Strategy Agent uses structured output to guarantee parseable JSON. This prevents raw markdown from reaching the UI.

## Auth Flow

```
POST /auth/signup → creates org + admin user → returns JWT
POST /auth/login  → verifies bcrypt hash → returns JWT
POST /auth/join   → validates invite_code → creates analyst user → returns JWT

JWT payload: { sub: user_id, org_id, role, exp }
```

## Data Models (key relationships)

```
Organization (1) ─── (*) User
Organization (1) ─── (1) OrgConfig
Organization (1) ─── (*) Category
Organization (1) ─── (*) Product
Product (1) ─── (*) CompetitorPrice
Product (1) ─── (*) DemandSignal
Product (1) ─── (*) PricingRecommendation
PricingRecommendation (1) ─── (*) RecommendationAction
PricingRecommendation (1) ─── (*) AuditLog
```

## Mock Data Architecture

### Competitor Prices
- 5 competitors per product (Amazon, Walmart, Target, BestBuy, Costco)
- 30-day price history generated via random walk (±3% daily volatility)

### Demand Signals
- Trend score: 0–100 (simulated Google Trends-style)
- Seasonal factor: category-based
- Velocity: units/day based on stock level

### Mock E-Commerce API
- Hosted at `POST /mock-ecommerce/update-price`
- 20% simulated failure rate (configurable via `MOCK_ECOMMERCE_FAILURE_RATE`)
- ExecutionAgent implements: try → on failure → log error + keep recommendation pending

## API Design Principles

- RESTful endpoints with meaningful status codes
- Consistent response format (`{"items": [...], "total": N}` for lists)
- Input validation via Pydantic schemas on all endpoints
- HTTP 400 for business rule violations, 401 for auth, 403 for RBAC, 404 for not found
