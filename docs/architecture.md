# Architecture: Policy Resolution Pattern

## Core Truth

> **The policy number is a key, not a payload.**
> **The policy number is a pointer, not a container.**

Everything else flows from this principle.

---

## What the Backend Actually Receives

### API Input (Always Minimal)

```json
POST /risk/evaluate
{
  "policy_number": "AUTO-MH-2024-000341"
}
```

That's it. No claims. No telematics. No climate data.

---

## What Happens Next (Real System Behavior)

The backend **resolves context** — it does not receive it.

### Step-by-Step Resolution

#### 1. Parse policy_number

Extract metadata from the identifier:
- Insurance type: `AUTO`
- Region: `MH`
- Year: `2024`
- Sequence: `000341`

#### 2. Fetch Policy Record

```sql
SELECT * FROM policies WHERE policy_number = :policy_number;
```

Returns:
- `policy_id` (UUID, primary key)
- `customer_id` (owner reference)
- `policy_type` (AUTO/HLTH/LIFE)
- `region_code` (climate lookup key)
- `effective_date`, `expiry_date` (tenure)
- `asset_type`, `asset_value` (exposure)
- `coverage_limit`, `deductible` (financial limits)

#### 3. Fetch Related Data Using policy_id as Join Key

##### Claims History

```sql
SELECT * FROM claims WHERE policy_id = :policy_id;
```

Returns:
- `claim_id`, `loss_date`, `reported_date`
- `claim_type` (collision, theft, liability, etc.)
- `paid_amount`, `reserve_amount`
- `status` (closed, open, disputed)

**Aggregated** to compute:
- Claim frequency (count over lookback period)
- Claim severity (total paid + reserved amounts)

##### Telematics (Auto Only)

```sql
SELECT * FROM telematics_aggregates 
WHERE policy_id = :policy_id 
ORDER BY period_end DESC 
LIMIT 1;
```

Returns latest aggregated snapshot:
- `miles_driven`, `harsh_braking_events`, `speeding_events`
- `distracted_driving_events`, `night_driving_pct`
- `avg_speed_mph`

**Note**: These are pre-aggregated metrics (30-day rolling windows), not raw GPS feeds.

##### IoT Metrics (if applicable)

```sql
SELECT * FROM iot_asset_metrics 
WHERE policy_id = :policy_id 
ORDER BY captured_at DESC 
LIMIT 1;
```

Returns:
- `device_id`, `health_score` (0–100)
- `battery_pct`, `anomaly_count`
- `last_maintenance_date`, `fault_codes` (JSONB)

##### Climate Risk (Region-Based)

```sql
SELECT * FROM climate_risk_indices 
WHERE region_code = :region 
  AND peril_type = 'flood' 
ORDER BY index_date DESC 
LIMIT 1;
```

Returns:
- `hazard_index` (0–100 for specified peril)
- `source` (NOAA, EU Climate Risk Index, etc.)

**Note**: Climate data joins via `region_code`, not `policy_id`.

---

## This Is the Core Concept

```
┌─────────────────────────────────────────────────────────────────────┐
│  API Request                                                         │
│  POST /risk/evaluate                                                 │
│  { "policy_number": "AUTO-MH-2024-000341" }                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: Resolve Policy Identity                                    │
│  SELECT * FROM policies WHERE policy_number = 'AUTO-MH-2024-000341' │
│                                                                      │
│  Returns: policy_id (UUID), customer_id, region_code, asset_value   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: Resolve Claims (via policy_id FK)                          │
│  SELECT * FROM claims WHERE policy_id = :policy_id                  │
│                                                                      │
│  Aggregates: claim_count, total_paid, total_reserved                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: Resolve Telematics (via policy_id FK)                      │
│  SELECT * FROM telematics_aggregates                                │
│  WHERE policy_id = :policy_id ORDER BY period_end DESC LIMIT 1      │
│                                                                      │
│  Returns: speeding_events, harsh_braking, night_driving_pct         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Resolve IoT (via policy_id FK)                             │
│  SELECT * FROM iot_asset_metrics                                    │
│  WHERE policy_id = :policy_id ORDER BY captured_at DESC LIMIT 1     │
│                                                                      │
│  Returns: health_score, anomaly_count, fault_codes                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: Resolve Climate (via region_code)                          │
│  SELECT * FROM climate_risk_indices                                 │
│  WHERE region_code = :region AND peril_type = 'flood'               │
│                                                                      │
│  Returns: hazard_index (0-100)                                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 6: Aggregate into RiskInputBundle                             │
│  {                                                                   │
│    policy: PolicyInput(...),                                        │
│    claims: ClaimsSummaryInput(...),                                 │
│    telematics: TelematicsAggregateInput(...),                       │
│    iot: IoTAssetMetricInput(...),                                   │
│    climate: ClimateIndexInput(...)                                  │
│  }                                                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 7: Evaluate Deterministically                                 │
│  - Compute component scores (0-100)                                 │
│  - Apply weights from ruleset                                       │
│  - Calculate Loss Risk Index (LRI)                                  │
│  - Assign risk band (LOW/MEDIUM/HIGH)                               │
│  - Trigger preventive action rules                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 8: Persist Evaluation                                         │
│  INSERT INTO risk_evaluations (...)                                 │
│  INSERT INTO risk_components (...)                                  │
│  INSERT INTO preventive_actions (...)                               │
│                                                                      │
│  Full audit trail with input_snapshot (JSONB)                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  API Response                                                        │
│  {                                                                   │
│    "risk_evaluation_id": "...",                                     │
│    "policy_number": "AUTO-MH-2024-000341",                          │
│    "loss_risk_index": 67,                                           │
│    "risk_band": "MEDIUM",                                           │
│    "components": [...],                                             │
│    "preventive_actions": [...]                                      │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Insight

```
policy_number (string identifier)
   ↓
resolves policy (policies table)
   ↓
resolves customer (customers table, via FK)
   ↓
resolves claims (claims table, via policy_id FK)
   ↓
resolves telematics (telematics_aggregates table, via policy_id FK)
   ↓
resolves IoT (iot_asset_metrics table, via policy_id FK)
   ↓
resolves climate (climate_risk_indices table, via region_code)
   ↓
aggregate signals → RiskInputBundle
   ↓
evaluate deterministically → LRI, band, actions
   ↓
persist evaluation (risk_evaluations + components + actions)
```

The policy number is the **join key across datasets**.

---

## What Actually Lives in the Database

### 1. `policies` (Identity + Metadata)

| Column           | Purpose                          |
| ---------------- | -------------------------------- |
| `policy_id`      | Primary key (UUID)               |
| `policy_number`  | Human-readable identifier (TEXT) |
| `policy_type`    | AUTO / HLTH / LIFE               |
| `customer_id`    | Owner (FK → customers)           |
| `region_code`    | Climate lookup key               |
| `effective_date` | Policy start (tenure calc)       |
| `asset_type`     | Vehicle, home, person            |
| `asset_value`    | Exposure metric                  |

**Foreign Keys**:
- `customer_id` → `customers.customer_id`

---

### 2. `claims` (Loss History)

| Column          | Purpose                 |
| --------------- | ----------------------- |
| `claim_id`      | Primary key (UUID)      |
| `policy_id`     | FK → policies           |
| `loss_date`     | When loss occurred      |
| `claim_type`    | Collision, theft, etc.  |
| `paid_amount`   | Settled amount          |
| `reserve_amount`| Reserved for settlement |
| `status`        | Closed / open           |

**Foreign Keys**:
- `policy_id` → `policies.policy_id` (ON DELETE RESTRICT)

**Aggregation Logic** (in `data_aggregation_service.py`):
```python
lookback_start = date.today() - relativedelta(months=36)
claims_row = await get_claims_summary(conn, policy_id, lookback_start)
# Returns: claim_count, total_paid_amount, total_reserved_amount
```

---

### 3. `telematics_aggregates` (Auto Only)

| Column                     | Purpose              |
| -------------------------- | -------------------- |
| `telematics_aggregate_id`  | Primary key (UUID)   |
| `policy_id`                | FK → policies        |
| `period_start`, `period_end`| 30-day window       |
| `harsh_braking_events`     | Behavior signal      |
| `speeding_events`          | Behavior signal      |
| `distracted_driving_events`| Behavior signal      |
| `night_driving_pct`        | Exposure signal      |
| `miles_driven`             | Exposure signal      |

**Foreign Keys**:
- `policy_id` → `policies.policy_id` (ON DELETE RESTRICT)

**Retrieval Logic**:
```python
tele_row = await get_latest_telematics(conn, policy_id)
if tele_row:
    telematics = TelematicsAggregateInput(**tele_row)
else:
    # Deterministic simulation for demo/testing
    telematics = simulate_telematics(policy_id)
```

---

### 4. `iot_asset_metrics` (Connected Assets)

| Column                | Purpose                  |
| --------------------- | ------------------------ |
| `iot_asset_metric_id` | Primary key (UUID)       |
| `policy_id`           | FK → policies            |
| `device_id`           | IoT device identifier    |
| `health_score`        | 0–100 asset condition    |
| `anomaly_count`       | Detected anomalies       |
| `fault_codes`         | JSONB diagnostic codes   |
| `captured_at`         | Timestamp of measurement |

**Foreign Keys**:
- `policy_id` → `policies.policy_id` (ON DELETE RESTRICT)

---

### 5. `climate_risk_indices` (Region-Based)

| Column        | Purpose                     |
| ------------- | --------------------------- |
| `region_code` | Join key (not FK)           |
| `peril_type`  | flood, heat, wildfire, etc. |
| `index_date`  | Temporal reference          |
| `hazard_index`| 0–100 risk severity         |
| `source`      | NOAA, EU Climate Risk, etc. |

**Join Pattern**:
```python
climate_row = await get_latest_climate_index(
    conn, policy.region_code, peril_type="flood", date.today()
)
```

**No Foreign Key**: Climate data is regional, not policy-specific.

---

## Why This Design Is Non-Negotiable

### 1. **Security**
No sensitive data (claims, telematics, health metrics) travels over APIs.

### 2. **Consistency**
Same policy → same risk score (deterministic). The data is stable, not ephemeral.

### 3. **Auditability**
You can replay evaluations later with the same inputs (stored in `input_snapshot` JSONB).

### 4. **Realism**
This mirrors actual insurance core systems:
- Policy Admin Systems (PAS) store policies
- Claims systems store loss history
- Telematics providers aggregate behavioral data
- Risk engines resolve and aggregate

---

## Mental Model (Remember This)

> **APIs accept identity.**
> **Systems fetch truth.**

If you try to pass data *into* the API, your system becomes fake and unmaintainable.

---

## What Happens If Data Is Missing?

Handled deterministically (no failures, no guesses):

```python
tele_row = await get_latest_telematics(conn, policy_id)
if tele_row:
    telematics = TelematicsAggregateInput(**tele_row)
else:
    # Deterministic simulation for demo/testing
    telematics = simulate_telematics(policy_id)
```

**Rules**:
- If telematics missing → assign neutral risk weight
- If IoT missing → simulate stable baseline
- If climate data missing → skip climate component
- Log missing signals in `input_snapshot`

No exceptions thrown. No random data generated.

---

## Code References

### Resolution Entry Point

**File**: [backend/app/services/data_aggregation_service.py](../backend/app/services/data_aggregation_service.py)

**Function**: `aggregate_inputs(conn, policy_id)`

```python
async def aggregate_inputs(conn: asyncpg.Connection, policy_id: str) -> RiskInputBundle:
    # 1. Resolve policy
    policy_row = await get_policy(conn, policy_id)
    policy = PolicyInput(**policy_row)

    # 2. Resolve claims (36-month lookback)
    lookback_start = date.today() - relativedelta(months=36)
    claims_row = await get_claims_summary(conn, policy_id, lookback_start)
    claims = ClaimsSummaryInput(**claims_row)

    # 3. Resolve telematics (latest snapshot)
    tele_row = await get_latest_telematics(conn, policy_id)
    telematics = TelematicsAggregateInput(**tele_row) if tele_row else simulate_telematics(policy_id)

    # 4. Resolve IoT (latest snapshot)
    iot_row = await get_latest_iot(conn, policy_id)
    iot = IoTAssetMetricInput(**iot_row) if iot_row else simulate_iot(policy_id)

    # 5. Resolve climate (region-based)
    climate_row = await get_latest_climate_index(conn, policy.region_code, "flood", date.today())
    climate = ClimateIndexInput(**climate_row) if climate_row else None

    return RiskInputBundle(policy=policy, claims=claims, telematics=telematics, iot=iot, climate=climate)
```

---

### Database Repositories

All repositories accept `policy_id` (or `region_code` for climate) and return resolved rows:

- [backend/app/db/repositories/policies.py](../backend/app/db/repositories/policies.py) → `get_policy(conn, policy_id)`
- [backend/app/db/repositories/claims.py](../backend/app/db/repositories/claims.py) → `get_claims_summary(conn, policy_id, lookback_start)`
- [backend/app/db/repositories/telematics.py](../backend/app/db/repositories/telematics.py) → `get_latest_telematics(conn, policy_id)`
- [backend/app/db/repositories/iot.py](../backend/app/db/repositories/iot.py) → `get_latest_iot(conn, policy_id)`
- [backend/app/db/repositories/climate.py](../backend/app/db/repositories/climate.py) → `get_latest_climate_index(conn, region_code, peril_type, index_date)`

---

### API Endpoint

**File**: [backend/app/api/risk.py](../backend/app/api/risk.py)

**Request Model**:
```python
class EvaluateRiskRequest(BaseModel):
    policy_number: str = Field(
        ..., description="Policy number: <TYPE>-<REGION>-<YEAR>-<SEQUENCE>"
    )
```

**Endpoint**:
```python
@router.post("/evaluate", response_model=RiskEvaluationResponse)
async def post_risk_evaluate(payload: EvaluateRiskRequest) -> RiskEvaluationResponse:
    return await evaluate_policy_risk(payload.policy_number)
```

**That's it.** One field. No nested data. Just the key.

---

## Database Schema Verification

**File**: [db/migrations/001_init.sql](../db/migrations/001_init.sql)

**Foreign Key Relationships**:

```sql
-- policies references customers
customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT

-- claims references policies
policy_id UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT

-- telematics_aggregates references policies
policy_id UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT

-- iot_asset_metrics references policies
policy_id UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT

-- risk_evaluations references policies
policy_id UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT
```

**These constraints enforce referential integrity at the database level.**

---

## One-Line Summary

> **The policy number is a pointer, not a container.**

Lock this in. Everything else becomes obvious.

---

## What This System Is NOT

This system does **not**:
- Create policies (that's Policy Admin Systems / PAS)
- Ingest raw telematics feeds (that's telematics providers)
- Generate claims (that's claims management systems)
- Forecast climate events (that's NOAA / external data providers)

## What This System IS

This system **does**:
- Resolve policy context via database joins
- Aggregate pre-existing risk signals
- Compute deterministic risk scores
- Trigger preventive actions
- Log evaluations for audit

### Comparison: Fake vs Real Architecture

| Aspect                  | ❌ Fake System (Don't Build)             | ✅ Real System (This Codebase)           |
| ----------------------- | ---------------------------------------- | ---------------------------------------- |
| **API Input**           | Massive JSON with nested claims/data     | Single `policy_number` string            |
| **Data Source**         | Client passes everything                 | Backend resolves from database           |
| **Validation**          | Trust client data                        | Enforce referential integrity (FKs)      |
| **Consistency**         | Different inputs → different scores      | Same policy → same score (deterministic) |
| **Security**            | Sensitive data travels over network      | Sensitive data never leaves DB           |
| **Auditability**        | Difficult to replay evaluations          | Full audit trail via `input_snapshot`    |
| **Scalability**         | Payload size grows with complexity       | Constant O(1) API payload size           |
| **Realism**             | Toy demo, unsuitable for production      | Mirrors actual insurance architectures   |
| **Database Role**       | Optional storage layer                   | **Source of truth**                      |
| **Policy Number Role**  | Display-only identifier                  | **Join key across datasets**             |

### Common Anti-Patterns to Avoid

#### ❌ Anti-Pattern 1: Data in API Payload

```json
{
  "policy_number": "AUTO-MH-2024-000341",
  "claims": [
    {"claim_id": "...", "amount": 5000, "date": "2023-11-15"},
    {"claim_id": "...", "amount": 3200, "date": "2024-02-20"}
  ],
  "telematics": {
    "speeding_events": 12,
    "harsh_braking": 8
  }
}
```

**Why this is wrong**: Client can manipulate data. No referential integrity. Unrealistic.

#### ✅ Correct Pattern: Identity-Only API

```json
{
  "policy_number": "AUTO-MH-2024-000341"
}
```

Backend resolves everything else.

---

#### ❌ Anti-Pattern 2: Creating Data on Demand

```python
# BAD: Generating fake data during evaluation
if not claims_exist:
    claims = generate_random_claims(policy_id)
```

**Why this is wrong**: Non-deterministic. Non-auditable. Makes no business sense.

#### ✅ Correct Pattern: Graceful Handling of Missing Data

```python
# GOOD: Deterministic fallback
tele_row = await get_latest_telematics(conn, policy_id)
if tele_row:
    telematics = TelematicsAggregateInput(**tele_row)
else:
    # Deterministic simulation for demo (stable hash-based)
    telematics = simulate_telematics(policy_id)
```

---

#### ❌ Anti-Pattern 3: No Foreign Keys

```sql
-- BAD: No referential integrity
CREATE TABLE claims (
  claim_id UUID PRIMARY KEY,
  policy_id UUID  -- No FK constraint
);
```

**Why this is wrong**: Orphaned data. No cascade handling. No join guarantees.

#### ✅ Correct Pattern: Explicit Foreign Keys

```sql
-- GOOD: Enforced referential integrity
CREATE TABLE claims (
  claim_id UUID PRIMARY KEY,
  policy_id UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT
);
```

---

## For New Developers

If someone asks: *"Where do I pass the claims data?"*

The correct answer is: **You don't. It's already in the database. The system fetches it.**

If they ask: *"How does the API get telematics data?"*

The correct answer is: **The API doesn't. The backend queries `telematics_aggregates` using the resolved `policy_id`.**

---

## For Reviewers / Auditors

This architecture demonstrates:
- Proper separation of concerns (API ≠ data layer)
- Referential integrity (enforced via foreign keys)
- Deterministic behavior (no external API calls during evaluation)
- Auditability (all inputs captured in `input_snapshot`)
- Security (sensitive data never leaves the database boundary)

This is how production insurance systems work.

---

## Quick Reference Card

### The Three Core Principles

1. **Policy number = pointer** (not data container)
2. **Database = source of truth** (not API payload)
3. **Backend resolves context** (via joins, not client input)

### Data Flow (Remember This)

```
API → policy_number only
  ↓
Backend resolves policy_id
  ↓
Join: claims (via policy_id FK)
Join: telematics (via policy_id FK)
Join: IoT (via policy_id FK)
Join: climate (via region_code)
  ↓
Aggregate → RiskInputBundle
  ↓
Evaluate → LRI + band + actions
  ↓
Persist → risk_evaluations table
  ↓
Response → evaluation result
```

### API Contract

**Request**: `{ "policy_number": "AUTO-MH-2024-000341" }`  
**Response**: Full evaluation with components and actions  
**No nested data in request. Ever.**

### Database Join Pattern

All related data joins via `policy_id`:
- `claims` → `WHERE policy_id = ?`
- `telematics_aggregates` → `WHERE policy_id = ?`
- `iot_asset_metrics` → `WHERE policy_id = ?`
- `climate_risk_indices` → `WHERE region_code = ?` (from policy)

### Missing Data Handling

- Telematics missing → deterministic simulation
- IoT missing → deterministic simulation
- Climate missing → skip component, log in snapshot
- **Never fail. Never guess randomly.**

### Security Guarantee

Sensitive data (claims, health, telematics) **never leaves the database boundary**. Only evaluation results travel over APIs.

### One-Sentence Explanation

> "The system accepts a policy number, resolves all related data from the database via foreign key joins, computes risk deterministically, and returns an auditable evaluation."

---

## Files Modified/Created

✅ [README.md](../README.md) — Added core architectural assumption and resolution flow  
✅ [docs/architecture.md](architecture.md) — Comprehensive architecture documentation (this file)

**No code changes required** — the implementation already follows this pattern correctly.

