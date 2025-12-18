-- Migration: 004_multi_insurance_support
-- Purpose: Add multi-insurance support (AUTO/HLTH/LIFE) with policy-number routing and type-specific inputs.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Customers
CREATE TABLE IF NOT EXISTS customers (
  customer_id         TEXT PRIMARY KEY,
  full_name           TEXT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Policies: add policy_type + customer_id and validate policy_number prefix
ALTER TABLE policies
  ADD COLUMN IF NOT EXISTS policy_type TEXT;

ALTER TABLE policies
  ADD COLUMN IF NOT EXISTS customer_id TEXT;

UPDATE policies
SET policy_type = COALESCE(policy_type, CASE
  WHEN split_part(policy_number, '-', 1) IN ('AUTO','HLTH','LIFE') THEN split_part(policy_number, '-', 1)
  ELSE 'AUTO'
END);

UPDATE policies
SET customer_id = COALESCE(customer_id, insured_id);

ALTER TABLE policies
  ALTER COLUMN policy_type SET NOT NULL;

ALTER TABLE policies
  ALTER COLUMN customer_id SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'policies_policy_type_chk'
  ) THEN
    ALTER TABLE policies
      ADD CONSTRAINT policies_policy_type_chk
      CHECK (policy_type IN ('AUTO','HLTH','LIFE'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'policies_policy_number_prefix_chk'
  ) THEN
    ALTER TABLE policies
      ADD CONSTRAINT policies_policy_number_prefix_chk
      CHECK (split_part(policy_number, '-', 1) = policy_type);
  END IF;
END $$;

-- Create customer rows for existing policies
INSERT INTO customers (customer_id)
SELECT DISTINCT customer_id
FROM policies
ON CONFLICT DO NOTHING;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'policies_customer_fk'
  ) THEN
    ALTER TABLE policies
      ADD CONSTRAINT policies_customer_fk
      FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT;
  END IF;
END $$;

-- Risk evaluations: persist policy_number/policy_type and ruleset version snapshots
ALTER TABLE risk_evaluations
  ADD COLUMN IF NOT EXISTS policy_number TEXT;
ALTER TABLE risk_evaluations
  ADD COLUMN IF NOT EXISTS policy_type TEXT;
ALTER TABLE risk_evaluations
  ADD COLUMN IF NOT EXISTS ruleset_name TEXT;
ALTER TABLE risk_evaluations
  ADD COLUMN IF NOT EXISTS ruleset_version TEXT;
ALTER TABLE risk_evaluations
  ADD COLUMN IF NOT EXISTS rules_sha256 CHAR(64);

-- Backfill from joins
UPDATE risk_evaluations re
SET
  policy_number = COALESCE(re.policy_number, p.policy_number),
  policy_type = COALESCE(re.policy_type, p.policy_type),
  ruleset_name = COALESCE(re.ruleset_name, rv.ruleset_name),
  ruleset_version = COALESCE(re.ruleset_version, rv.version),
  rules_sha256 = COALESCE(re.rules_sha256, rv.rules_sha256)
FROM policies p, rule_versions rv
WHERE re.policy_id = p.policy_id
  AND rv.rule_version_id = re.rule_version_id;

ALTER TABLE risk_evaluations
  ALTER COLUMN policy_number SET NOT NULL;
ALTER TABLE risk_evaluations
  ALTER COLUMN policy_type SET NOT NULL;
ALTER TABLE risk_evaluations
  ALTER COLUMN ruleset_name SET NOT NULL;
ALTER TABLE risk_evaluations
  ALTER COLUMN ruleset_version SET NOT NULL;
ALTER TABLE risk_evaluations
  ALTER COLUMN rules_sha256 SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'risk_evaluations_policy_type_chk'
  ) THEN
    ALTER TABLE risk_evaluations
      ADD CONSTRAINT risk_evaluations_policy_type_chk
      CHECK (policy_type IN ('AUTO','HLTH','LIFE'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_risk_evals_policy_number_time ON risk_evaluations(policy_number, evaluated_at DESC);

-- Type-specific profile tables
CREATE TABLE IF NOT EXISTS health_policy_profiles (
  policy_id        UUID PRIMARY KEY REFERENCES policies(policy_id) ON DELETE CASCADE,
  member_age       INTEGER NOT NULL CHECK (member_age >= 0 AND member_age <= 120),
  chronic_flags    JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS life_policy_profiles (
  policy_id        UUID PRIMARY KEY REFERENCES policies(policy_id) ON DELETE CASCADE,
  insured_age      INTEGER NOT NULL CHECK (insured_age >= 0 AND insured_age <= 120),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mortality_risk_table (
  mortality_risk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  age_min           INTEGER NOT NULL,
  age_max           INTEGER NOT NULL,
  mortality_index   INTEGER NOT NULL CHECK (mortality_index >= 0 AND mortality_index <= 100),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (age_max >= age_min),
  UNIQUE (age_min, age_max)
);

COMMIT;
