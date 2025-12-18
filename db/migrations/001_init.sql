-- Migration: 001_init
-- Purpose: Initial schema for deterministic Loss Risk Index (LRI) evaluation platform.
-- Target: PostgreSQL (AWS RDS compatible)

BEGIN;

-- UUID generation (available on AWS RDS Postgres)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Shared updated_at trigger
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- -----------------------------
-- Core master data
-- -----------------------------

CREATE TABLE customers (
  customer_id         TEXT PRIMARY KEY,
  full_name           TEXT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_customers_set_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE policies (
  policy_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_number        TEXT NOT NULL UNIQUE,
  policy_type          TEXT NOT NULL CHECK (policy_type IN ('AUTO', 'HLTH', 'LIFE')),
  customer_id          TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
  insured_id           TEXT NOT NULL,
  product_line         TEXT NOT NULL,
  region_code          TEXT NOT NULL,
  asset_type           TEXT NOT NULL,
  asset_value          NUMERIC(14,2) NOT NULL CHECK (asset_value >= 0),
  coverage_limit       NUMERIC(14,2) NOT NULL CHECK (coverage_limit >= 0),
  deductible           NUMERIC(14,2) NOT NULL CHECK (deductible >= 0),
  effective_date       DATE NOT NULL,
  expiry_date          DATE NOT NULL,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (expiry_date > effective_date),
  -- Enforce <TYPE>-<REGION>-<YEAR>-<SEQUENCE> where TYPE must match policy_type
  CHECK (split_part(policy_number, '-', 1) = policy_type)
);

CREATE TRIGGER trg_policies_set_updated_at
BEFORE UPDATE ON policies
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE claims (
  claim_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_id            UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT,
  loss_date            DATE NOT NULL,
  reported_date        DATE NOT NULL,
  claim_type           TEXT NOT NULL,
  status               TEXT NOT NULL,
  paid_amount          NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
  reserve_amount       NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (reserve_amount >= 0),
  description          TEXT NULL,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (reported_date >= loss_date)
);

CREATE INDEX idx_claims_policy_id ON claims(policy_id);
CREATE INDEX idx_claims_loss_date ON claims(loss_date);

CREATE TRIGGER trg_claims_set_updated_at
BEFORE UPDATE ON claims
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- -----------------------------
-- Deterministic input aggregates (telematics / IoT / climate)
-- -----------------------------

CREATE TABLE telematics_aggregates (
  telematics_aggregate_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_id                UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT,
  period_start             DATE NOT NULL,
  period_end               DATE NOT NULL,
  miles_driven             NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (miles_driven >= 0),
  harsh_braking_events     INTEGER NOT NULL DEFAULT 0 CHECK (harsh_braking_events >= 0),
  speeding_events          INTEGER NOT NULL DEFAULT 0 CHECK (speeding_events >= 0),
  distracted_driving_events INTEGER NOT NULL DEFAULT 0 CHECK (distracted_driving_events >= 0),
  night_driving_pct        NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (night_driving_pct >= 0 AND night_driving_pct <= 100),
  avg_speed_mph            NUMERIC(6,2) NULL CHECK (avg_speed_mph IS NULL OR avg_speed_mph >= 0),
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (period_end >= period_start),
  UNIQUE (policy_id, period_start, period_end)
);

CREATE INDEX idx_telematics_policy_period ON telematics_aggregates(policy_id, period_start, period_end);

CREATE TABLE iot_asset_metrics (
  iot_asset_metric_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_id             UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT,
  captured_at           TIMESTAMPTZ NOT NULL,
  device_id             TEXT NOT NULL,
  health_score          INTEGER NOT NULL CHECK (health_score >= 0 AND health_score <= 100),
  battery_pct           INTEGER NULL CHECK (battery_pct IS NULL OR (battery_pct >= 0 AND battery_pct <= 100)),
  anomaly_count         INTEGER NOT NULL DEFAULT 0 CHECK (anomaly_count >= 0),
  last_maintenance_date DATE NULL,
  fault_codes           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_iot_policy_captured_at ON iot_asset_metrics(policy_id, captured_at DESC);
CREATE INDEX idx_iot_device_id ON iot_asset_metrics(device_id);

CREATE TABLE climate_risk_indices (
  climate_risk_index_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region_code           TEXT NOT NULL,
  peril_type            TEXT NOT NULL,
  index_date            DATE NOT NULL,
  hazard_index          INTEGER NOT NULL CHECK (hazard_index >= 0 AND hazard_index <= 100),
  source                TEXT NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (region_code, peril_type, index_date)
);

CREATE INDEX idx_climate_region_date ON climate_risk_indices(region_code, index_date DESC);

-- -----------------------------
-- Ruleset versioning
-- -----------------------------

CREATE TABLE rule_versions (
  rule_version_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ruleset_name        TEXT NOT NULL,
  version             TEXT NOT NULL,
  rules_sha256        CHAR(64) NOT NULL,
  rules_document      JSONB NOT NULL,
  created_by          TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (ruleset_name, version),
  UNIQUE (ruleset_name, rules_sha256)
);

-- -----------------------------
-- Risk evaluations (auditable outputs)
-- -----------------------------

CREATE TABLE risk_evaluations (
  risk_evaluation_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_id           UUID NOT NULL REFERENCES policies(policy_id) ON DELETE RESTRICT,
  policy_number       TEXT NOT NULL,
  policy_type         TEXT NOT NULL CHECK (policy_type IN ('AUTO', 'HLTH', 'LIFE')),
  evaluated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  loss_risk_index     INTEGER NOT NULL CHECK (loss_risk_index >= 0 AND loss_risk_index <= 100),
  risk_band           TEXT NOT NULL CHECK (risk_band IN ('LOW', 'MEDIUM', 'HIGH')),
  rule_version_id     UUID NOT NULL REFERENCES rule_versions(rule_version_id) ON DELETE RESTRICT,
  ruleset_name        TEXT NOT NULL,
  ruleset_version     TEXT NOT NULL,
  rules_sha256        CHAR(64) NOT NULL,
  input_snapshot      JSONB NOT NULL,
  explanation         JSONB NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_evals_policy_time ON risk_evaluations(policy_id, evaluated_at DESC);
CREATE INDEX idx_risk_evals_rule_version ON risk_evaluations(rule_version_id);
CREATE INDEX idx_risk_evals_policy_number_time ON risk_evaluations(policy_number, evaluated_at DESC);

CREATE TABLE risk_components (
  risk_component_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  risk_evaluation_id  UUID NOT NULL REFERENCES risk_evaluations(risk_evaluation_id) ON DELETE CASCADE,
  component_name      TEXT NOT NULL,
  raw_value           NUMERIC NULL,
  normalized_score    INTEGER NOT NULL CHECK (normalized_score >= 0 AND normalized_score <= 100),
  weight              NUMERIC(6,4) NOT NULL CHECK (weight >= 0),
  weighted_score      NUMERIC(10,4) NOT NULL CHECK (weighted_score >= 0),
  details             JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (risk_evaluation_id, component_name)
);

CREATE INDEX idx_risk_components_eval ON risk_components(risk_evaluation_id);

CREATE TABLE preventive_actions (
  preventive_action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  risk_evaluation_id   UUID NOT NULL REFERENCES risk_evaluations(risk_evaluation_id) ON DELETE CASCADE,
  rule_id              TEXT NOT NULL,
  action_type          TEXT NOT NULL,
  action_payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
  priority             INTEGER NOT NULL DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
  status               TEXT NOT NULL DEFAULT 'RECOMMENDED' CHECK (status IN ('RECOMMENDED', 'ACKNOWLEDGED', 'DISMISSED', 'EXECUTED')),
  rationale            TEXT NOT NULL,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_actions_eval ON preventive_actions(risk_evaluation_id);
CREATE INDEX idx_actions_rule_id ON preventive_actions(rule_id);

-- -----------------------------
-- Deterministic agent orchestration logs (CrewAI)
-- -----------------------------

CREATE TABLE agent_logs (
  agent_log_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  risk_evaluation_id  UUID NULL REFERENCES risk_evaluations(risk_evaluation_id) ON DELETE CASCADE,
  policy_id           UUID NULL REFERENCES policies(policy_id) ON DELETE RESTRICT,
  agent_name          TEXT NOT NULL,
  task_name           TEXT NOT NULL,
  status              TEXT NOT NULL CHECK (status IN ('STARTED', 'SUCCEEDED', 'FAILED')),
  started_at          TIMESTAMPTZ NOT NULL,
  finished_at         TIMESTAMPTZ NULL,
  input_payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_payload      JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message       TEXT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE INDEX idx_agent_logs_eval ON agent_logs(risk_evaluation_id);
CREATE INDEX idx_agent_logs_policy_time ON agent_logs(policy_id, started_at DESC);

COMMIT;
