# Architecture and Technical Decisions

This document outlines the core technical and product decisions made during the development of PriceIQ, addressing trade-offs and rationale.

## 1. Multi-Agent Orchestration via LLM Tool Calling (The "Dynamic Agent" Pattern)
**Context:** Initially, we considered a strict, hardcoded sequential pipeline (Agent A -> Agent B -> Agent C).
**Decision:** We implemented an autonomous orchestrator using LLM Tool Calling.
**Rationale:** Real-world pricing requires dynamic analysis. Sometimes inventory is the most critical factor; sometimes it's a competitor's sudden price drop. By giving the primary Strategy Agent access to sub-agents as "tools" (`analyze_market`, `analyze_inventory`, `analyze_demand`), the LLM can decide which data it needs and in what order, creating a much more robust and adaptable AI system.

## 2. Multi-Tenancy Architecture (Shared Database, Isolated Rows)
**Context:** How to isolate data for different e-commerce organizations using the SaaS platform.
**Decision:** We implemented row-level isolation using an `org_id` foreign key on all tenant-scoped tables, enforced by a FastAPI Dependency injection (`TenantContext`).
**Rationale:** Creating separate databases per tenant is too resource-intensive for an MVP. Row-level isolation is standard practice and highly scalable. By enforcing the filter automatically in the `get_tenant_ctx` middleware, we prevent developers from accidentally leaking data across tenants.

## 3. Human-in-the-Loop Execution Engine
**Context:** How to apply the AI's recommended prices to the actual e-commerce storefront.
**Decision:** We introduced the `Execution Agent` with configurable auto-execute thresholds and a strict Audit Trail. 
**Rationale:** Fully autonomous AI pricing is dangerous for merchants. We built a safety mechanism where high-confidence recommendations (>85%) are executed automatically, but borderline recommendations are queued for human review. Furthermore, all executions (successful or failed) are recorded in an immutable Audit Log for accountability.

## 4. Groq + Llama 3 for LLM Infrastructure
**Context:** We needed a fast, structured output LLM for the agentic reasoning loop.
**Decision:** We selected Groq inference using Llama 3 models over standard OpenAI GPT-4.
**Rationale:** Groq provides ultra-low latency, which is essential for a system that runs up to 8 reasoning steps per product in a single API call. It supports native JSON structured output and tool calling, perfectly mapping to our Pydantic schemas.

## 5. Next.js 14 + Tailwind UI
**Context:** Choosing a frontend framework.
**Decision:** Next.js 14 (React) with Tailwind CSS.
**Rationale:** Next.js provides excellent routing and state management capabilities needed for a complex dashboard. Tailwind allows for rapid, clean, and consistent UI development, ensuring the product feels professional and usable out of the box.

## 6. Pydantic Validation for AI Output
**Context:** LLMs hallucinate field names and data types.
**Decision:** We force the LLM to return a strict JSON schema and run it directly through FastAPI/Pydantic validation models (`RecommendationOut`).
**Rationale:** This ensures the frontend *never* receives malformed data, preventing UI crashes. We also implemented explicit backend error catching so that if the AI pipeline fails, a proper HTTP 500 error is passed to the UI for graceful handling.

## 7. What trade-offs did you make given the 5-day timeline?
- **Mocked Integrations:** Instead of integrating with a real Shopify, Amazon, or ERP API, we built a mock e-commerce endpoint and a complex seeding script to simulate real-world data.
- **Database:** We utilized SQLite (via SQLAlchemy) for rapid local development rather than standing up a fully managed PostgreSQL instance.
- **Synchronous Processing:** The AI loop currently runs synchronously within the API request. On a massive catalog, this could lead to HTTP timeouts.

## 8. What would you improve with 2 more weeks?
- **Real Integrations:** Implement OAuth connections to real e-commerce platforms (Shopify/WooCommerce) to pull live product/inventory data and execute real price changes.
- **Background Task Queues:** Move the AI orchestration loop into an asynchronous background worker (using Celery or Redis) to prevent HTTP timeouts when analyzing hundreds of products.
- **A/B Testing & Analytics:** Build features to track the historical conversion rates of AI-recommended prices versus human-set prices to prove ROI.
- **Database Migration:** Migrate from SQLite to PostgreSQL for robust concurrent access and better production scale.

## 9. What was the hardest part and how did you solve it?
**The Hardest Part:** Managing LLM unreliability, specifically loops getting stuck, timeouts, and hallucinating invalid JSON structures that would crash the frontend UI.

**The Solution:** 
1. **Bounded Loops:** We wrapped the agentic loop in a strict `for _ in range(8)` loop. If the LLM doesn't reach a conclusion in 8 steps, it forcibly terminates.
2. **Fallback Mechanisms:** If the LLM fails completely, the orchestrator triggers a hardcoded fallback that retains the current price and logs an "orchestration failure" rationale.
3. **Pydantic Boundaries:** We enforce strict Pydantic schema validation at the API boundary. This ensures that even if the AI misbehaves, the frontend *always* receives the data structure it expects, preventing application crashes.
