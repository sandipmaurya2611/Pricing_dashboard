# PriceIQ — Dynamic Pricing Intelligence Dashboard

> AI-powered multi-agent pricing system with human-in-the-loop approval workflow.

## Live Demo
- **Frontend**: https://priceiq.vercel.app (or localhost:3000)
- **Backend API Docs**: http://localhost:8000/docs

## Demo Credentials
| Role | Email | Password |
|---|---|---|
| Admin | admin@klypup.com | Admin@123 |
| Analyst | analyst@klypup.com | Analyst@123 |

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Copy and fill env
cp .env.example .env
# Add your OPENAI_API_KEY, DATABASE_URL

# Run migrations + seed data
alembic upgrade head
python scripts/seed.py

# Start server
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Architecture
See [ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Decisions
See [DECISIONS.md](docs/DECISIONS.md)

## Multi-Agent System

The AI pipeline runs 5 specialized agents:

1. **Market Intelligence Agent** — Competitor price retrieval + trend analysis
2. **Demand Forecasting Agent** — Elasticity, velocity, seasonal patterns
3. **Inventory & Cost Agent** — Margin floor enforcement, stock status
4. **Pricing Strategy Agent** — Central orchestrator, final recommendation
5. **Execution & Compliance Agent** — Auto-execute or route to human review

Agents 1, 3 run in **parallel** → Agent 2 uses their outputs → Agent 4 synthesizes → Agent 5 executes.

## API Documentation

Full OpenAPI docs available at `/docs` when the backend is running.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **AI**: OpenAI GPT-4o (function calling + structured JSON output)
- **Frontend**: Next.js 14, Tailwind CSS, Recharts, Zustand
- **Auth**: JWT (python-jose + bcrypt)
- **Multi-tenancy**: org_id column + tenant context middleware
