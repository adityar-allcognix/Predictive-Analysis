-- Migration: 002_seed_demo
-- Purpose: Minimal deterministic demo data for local development.

BEGIN;

INSERT INTO customers (customer_id, full_name)
VALUES ('CUST-0001', 'Demo Customer')
ON CONFLICT (customer_id) DO NOTHING;

-- Stable demo policy UUID for repeatable testing
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '00000000-0000-0000-0000-000000000001'::uuid,
  'AUTO-MH-2025-000001',
  'AUTO',
  'CUST-0001',
  'INSURED-0001',
  'commercial-auto',
  'US-FL',
  'vehicle',
  55000.00,
  100000.00,
  2500.00,
  '2025-01-01',
  '2026-01-01'
)
ON CONFLICT (policy_number) DO NOTHING;

INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '00000000-0000-0000-0000-000000000002'::uuid,
  'HLTH-MH-2025-000001',
  'HLTH',
  'CUST-0001',
  'INSURED-0001',
  'health',
  'IN-MH',
  'member',
  0.00,
  0.00,
  0.00,
  '2025-01-01',
  '2026-01-01'
)
ON CONFLICT (policy_number) DO NOTHING;

INSERT INTO health_policy_profiles (policy_id, member_age, chronic_flags)
VALUES (
  '00000000-0000-0000-0000-000000000002'::uuid,
  46,
  '{"diabetes": true, "hypertension": false}'::jsonb
)
ON CONFLICT (policy_id) DO NOTHING;

INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '00000000-0000-0000-0000-000000000003'::uuid,
  'LIFE-IN-2025-000001',
  'LIFE',
  'CUST-0001',
  'INSURED-0001',
  'life',
  'IN',
  'insured',
  0.00,
  0.00,
  0.00,
  '2022-01-01',
  '2042-01-01'
)
ON CONFLICT (policy_number) DO NOTHING;

INSERT INTO life_policy_profiles (policy_id, insured_age)
VALUES (
  '00000000-0000-0000-0000-000000000003'::uuid,
  52
)
ON CONFLICT (policy_id) DO NOTHING;

-- Seed a minimal mortality table if empty
INSERT INTO mortality_risk_table (mortality_risk_id, age_min, age_max, mortality_index)
SELECT gen_random_uuid(), v.age_min, v.age_max, v.mortality_index
FROM (VALUES
  (0, 29, 10),
  (30, 44, 25),
  (45, 59, 55),
  (60, 69, 75),
  (70, 120, 95)
) AS v(age_min, age_max, mortality_index)
WHERE NOT EXISTS (SELECT 1 FROM mortality_risk_table);

-- A couple claims in last 36 months
INSERT INTO claims (
  claim_id, policy_id, loss_date, reported_date, claim_type, status, paid_amount, reserve_amount, description
)
VALUES
(
  gen_random_uuid(),
  '00000000-0000-0000-0000-000000000001'::uuid,
  '2025-08-12',
  '2025-08-13',
  'collision',
  'closed',
  4200.00,
  0.00,
  'Rear-end collision'
),
(
  gen_random_uuid(),
  '00000000-0000-0000-0000-000000000001'::uuid,
  '2024-11-02',
  '2024-11-03',
  'comprehensive',
  'closed',
  900.00,
  0.00,
  'Windshield damage'
)
ON CONFLICT DO NOTHING;

-- Climate hazard index for the region (peril=flood)
INSERT INTO climate_risk_indices (
  climate_risk_index_id, region_code, peril_type, index_date, hazard_index, source
)
VALUES
(
  gen_random_uuid(),
  'US-FL',
  'flood',
  '2025-12-01',
  72,
  'demo-static'
)
ON CONFLICT (region_code, peril_type, index_date) DO NOTHING;

COMMIT;