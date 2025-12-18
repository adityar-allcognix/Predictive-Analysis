# Predictive Analytics for Loss Prevention (Deterministic)

Enterprise-style, **rule-based** Predictive Analytics platform for insurance loss prevention.

**Non-negotiables**
- Deterministic, auditable, extensible
- No ML training, no learning, no randomness
- CrewAI is used for orchestration structure/logging only; decisions come from explicit formulas + rule definitions

## Core Architectural Assumption

> **The system assumes all policies and related risk data already exist in internal databases. The platform evaluates loss risk deterministically using resolved policy context.**

This system does **not** create policies or ingest raw data. It is an **evaluation engine** that:
- Receives a `policy_id` (the join key, not a data payload)
- Resolves policy context from normalized database tables via foreign key relationships
- Aggregates risk signals from pre-existing claims, telematics, IoT, and climate data
- Computes deterministic risk scores and triggers preventive actions

**Key principle**: The policy number is a **pointer**, not a container.

## What it does
Given a `policy_number`, the platform:
1. Aggregates data (policy + claims + telematics + IoT + climate)
2. Computes bounded component scores (0–100)
3. Computes Loss Risk Index (LRI) 0–100 using weighted deterministic formula
4. Assigns a risk band: `LOW` / `MEDIUM` / `HIGH`
5. Applies explicit preventive-action rules
6. Persists evaluation + components + actions + rule version + agent logs
7. Returns a fully explainable JSON response

## Multi-insurance support (strict separation)
The platform supports **exactly** these policy types:
- `AUTO` (uses claims + telematics + IoT + climate + exposure)
- `HLTH` (uses age + claims severity + chronic indicators only)
- `LIFE` (uses age + tenure + static mortality index only)

Routing is by policy number prefix. Format:
- `<INSURANCE_TYPE>-<REGION>-<YEAR>-<SEQUENCE>` (e.g. `AUTO-MH-2025-000001`)

## Architecture: Context Resolution Pattern

### API Input (Minimal by Design)
```json
{
  "policy_number": "AUTO-MH-2024-000341"
}
```

No claims, telematics, or climate data is passed to the API.

### Backend Resolution Flow
The backend **resolves context** via database joins:

1. **Parse policy_number** → Extract insurance type (`AUTO`) and region (`MH`)
2. **Fetch policy record** → `SELECT * FROM policies WHERE policy_number = ?`
   - Returns: customer_id, policy_type, start_date, asset metadata
3. **Fetch related data using policy_id as join key**:
   - **Claims**: `SELECT * FROM claims WHERE policy_id = ?`
   - **Telematics**: `SELECT * FROM telematics_aggregates WHERE policy_id = ?`
   - **IoT**: `SELECT * FROM iot_asset_metrics WHERE policy_id = ?`
   - **Climate**: `SELECT * FROM climate_risk_indices WHERE region = ?`
4. **Aggregate signals** → Build `RiskInputBundle`
5. **Evaluate deterministically** → Compute LRI, band, actions
6. **Persist evaluation** → Full audit trail

### Why This Design

- **Security**: No sensitive data travels over APIs
- **Consistency**: Same policy → same risk score (deterministic)
- **Auditability**: Evaluations can be replayed with original data
- **Realism**: Mirrors actual insurance core systems

The policy number is the **join key** across datasets, not a data container.

## Repository layout
- [backend](backend) FastAPI + deterministic engine + persistence
- [db](db) Postgres migrations
- [frontend](frontend) Next.js dashboard
- [docs](docs) model documentation
  - [architecture.md](docs/architecture.md) — **Policy resolution pattern (read this first)**
  - [risk_model.md](docs/risk_model.md) — Risk scoring formulas and rules

## Database
### Start Postgres (local)
From repo root:
- `docker compose up -d`

### Apply migrations
- `psql "postgresql://postgres:postgres@localhost:5433/predictive_analysis" -f db/migrations/001_init.sql`
- `psql "postgresql://postgres:postgres@localhost:5433/predictive_analysis" -f db/migrations/004_multi_insurance_support.sql`
- `psql "postgresql://postgres:postgres@localhost:5433/predictive_analysis" -f db/migrations/002_seed_demo.sql`
- `psql "postgresql://postgres:postgres@localhost:5433/predictive_analysis" -f db/migrations/003_add_rule_id_to_preventive_actions.sql`

The seed migration inserts stable demo policies:
- `AUTO-MH-2025-000001`
- `HLTH-MH-2025-000001`
- `LIFE-IN-2025-000001`

**Indian Test Data** (comprehensive testing dataset):
- `psql "postgresql://postgres:postgres@localhost:5433/predictive_analysis" -f db/migrations/005_seed_indian_data.sql`
- Adds 10 policies (5 AUTO, 3 HLTH, 2 LIFE) across Mumbai, Delhi, Bangalore, Chennai, Pune
- Includes claims, telematics, IoT, and climate data
- See [QUICKSTART_TESTING.md](QUICKSTART_TESTING.md) for test commands

## Backend (FastAPI)
### Setup
- `cd backend`
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- `cp .env.example .env` (edit `DATABASE_URL` if needed)

### Run
- `uvicorn app.main:app --reload --port 8000`

### API
- `POST /risk/evaluate` with body `{ "policy_number": "AUTO-MH-2025-000001" }`
- `GET /risk/{policy_number}`

### Test with cURL
```bash
# Evaluate risk for a policy
curl -X POST http://localhost:8000/risk/evaluate \
  -H "Content-Type: application/json" \
  -d '{"policy_number": "AUTO-MH-2024-000341"}' | jq

# Get latest evaluation
curl -X GET http://localhost:8000/risk/AUTO-MH-2024-000341 | jq
```

**See [QUICKSTART_TESTING.md](QUICKSTART_TESTING.md) for comprehensive testing guide with Indian data.**

## Frontend (Next.js)
### Setup
- `cd frontend`
- `npm install`
- `cp .env.example .env.local`

### Run
- `npm run dev`
- Open `http://localhost:3000`

## Deterministic risk model
- Rulesets and weights:
	- [backend/app/risk/rules/auto_ruleset_v1.json](backend/app/risk/rules/auto_ruleset_v1.json)
	- [backend/app/risk/rules/health_ruleset_v1.json](backend/app/risk/rules/health_ruleset_v1.json)
	- [backend/app/risk/rules/life_ruleset_v1.json](backend/app/risk/rules/life_ruleset_v1.json)
- Documentation: [docs/risk_model.md](docs/risk_model.md)

## CrewAI posture
CrewAI is kept strictly as an orchestration boundary:
- Agents are stateless
- Outputs used for decisions are computed by deterministic Python code
- Agent execution is logged to `agent_logs` for audit

If CrewAI is installed, [backend/app/agents/crewai_orchestrator.py](backend/app/agents/crewai_orchestrator.py) provides a CrewAI-compatible wrapper that preserves determinism.
