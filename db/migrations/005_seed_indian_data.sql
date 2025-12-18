-- Migration: 005_seed_indian_data
-- Purpose: Comprehensive Indian data for testing across multiple regions and insurance types

BEGIN;

-- Indian customers
INSERT INTO customers (customer_id, full_name)
VALUES 
  ('CUST-IN-0001', 'Rajesh Kumar'),
  ('CUST-IN-0002', 'Priya Sharma'),
  ('CUST-IN-0003', 'Amit Patel'),
  ('CUST-IN-0004', 'Neha Singh'),
  ('CUST-IN-0005', 'Vikram Desai'),
  ('CUST-IN-0006', 'Anjali Reddy'),
  ('CUST-IN-0007', 'Sanjay Mehta'),
  ('CUST-IN-0008', 'Kavita Nair'),
  ('CUST-IN-0009', 'Arjun Gupta'),
  ('CUST-IN-0010', 'Pooja Iyer')
ON CONFLICT (customer_id) DO NOTHING;

-- ========================================
-- AUTO Insurance Policies (Indian Regions)
-- ========================================

-- 1. Mumbai (MH) - High risk driver
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '10000000-0000-0000-0000-000000000001'::uuid,
  'AUTO-MH-2024-000341',
  'AUTO',
  'CUST-IN-0001',
  'INSURED-IN-0001',
  'private-auto',
  'IN-MH',
  'vehicle',
  1250000.00, -- ₹12.5 lakh (sedan)
  2000000.00,
  25000.00,
  '2024-01-15',
  '2025-01-15'
)
ON CONFLICT (policy_number) DO NOTHING;

-- 2. Delhi (DL) - Moderate risk
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '10000000-0000-0000-0000-000000000002'::uuid,
  'AUTO-DL-2024-000542',
  'AUTO',
  'CUST-IN-0002',
  'INSURED-IN-0002',
  'private-auto',
  'IN-DL',
  'vehicle',
  850000.00, -- ₹8.5 lakh (hatchback)
  1500000.00,
  15000.00,
  '2024-03-20',
  '2025-03-20'
)
ON CONFLICT (policy_number) DO NOTHING;

-- 3. Bangalore (KA) - Low risk driver
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '10000000-0000-0000-0000-000000000003'::uuid,
  'AUTO-KA-2024-001023',
  'AUTO',
  'CUST-IN-0003',
  'INSURED-IN-0003',
  'commercial-auto',
  'IN-KA',
  'vehicle',
  2100000.00, -- ₹21 lakh (SUV)
  3000000.00,
  35000.00,
  '2024-06-10',
  '2025-06-10'
)
ON CONFLICT (policy_number) DO NOTHING;

-- 4. Chennai (TN) - High claim frequency
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '10000000-0000-0000-0000-000000000004'::uuid,
  'AUTO-TN-2024-000678',
  'AUTO',
  'CUST-IN-0004',
  'INSURED-IN-0004',
  'private-auto',
  'IN-TN',
  'vehicle',
  950000.00, -- ₹9.5 lakh
  1800000.00,
  20000.00,
  '2024-02-01',
  '2025-02-01'
)
ON CONFLICT (policy_number) DO NOTHING;

-- 5. Pune (MH) - Clean record
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '10000000-0000-0000-0000-000000000005'::uuid,
  'AUTO-MH-2024-000892',
  'AUTO',
  'CUST-IN-0005',
  'INSURED-IN-0005',
  'private-auto',
  'IN-MH',
  'vehicle',
  1450000.00, -- ₹14.5 lakh
  2500000.00,
  30000.00,
  '2024-04-12',
  '2025-04-12'
)
ON CONFLICT (policy_number) DO NOTHING;

-- ========================================
-- HEALTH Insurance Policies
-- ========================================

-- 6. Health - Mumbai, younger member
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '20000000-0000-0000-0000-000000000001'::uuid,
  'HLTH-MH-2024-000123',
  'HLTH',
  'CUST-IN-0006',
  'INSURED-IN-0006',
  'health',
  'IN-MH',
  'member',
  0.00,
  500000.00, -- ₹5 lakh coverage
  0.00,
  '2024-01-01',
  '2025-01-01'
)
ON CONFLICT (policy_number) DO NOTHING;

INSERT INTO health_policy_profiles (policy_id, member_age, chronic_flags)
VALUES (
  '20000000-0000-0000-0000-000000000001'::uuid,
  32,
  '{}'::jsonb -- No chronic conditions
)
ON CONFLICT (policy_id) DO NOTHING;

-- 7. Health - Delhi, middle-aged with diabetes
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '20000000-0000-0000-0000-000000000002'::uuid,
  'HLTH-DL-2024-000456',
  'HLTH',
  'CUST-IN-0007',
  'INSURED-IN-0007',
  'health',
  'IN-DL',
  'member',
  0.00,
  1000000.00, -- ₹10 lakh coverage
  0.00,
  '2024-02-15',
  '2025-02-15'
)
ON CONFLICT (policy_number) DO NOTHING;

INSERT INTO health_policy_profiles (policy_id, member_age, chronic_flags)
VALUES (
  '20000000-0000-0000-0000-000000000002'::uuid,
  48,
  '{"diabetes": true, "hypertension": false}'::jsonb
)
ON CONFLICT (policy_id) DO NOTHING;

-- 8. Health - Bangalore, senior with multiple conditions
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '20000000-0000-0000-0000-000000000003'::uuid,
  'HLTH-KA-2024-000789',
  'HLTH',
  'CUST-IN-0008',
  'INSURED-IN-0008',
  'health',
  'IN-KA',
  'member',
  0.00,
  750000.00, -- ₹7.5 lakh
  0.00,
  '2024-03-01',
  '2025-03-01'
)
ON CONFLICT (policy_number) DO NOTHING;

INSERT INTO health_policy_profiles (policy_id, member_age, chronic_flags)
VALUES (
  '20000000-0000-0000-0000-000000000003'::uuid,
  64,
  '{"diabetes": true, "hypertension": true, "heart_disease": false}'::jsonb
)
ON CONFLICT (policy_id) DO NOTHING;

-- ========================================
-- LIFE Insurance Policies
-- ========================================

-- 9. Life - Young professional
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '30000000-0000-0000-0000-000000000001'::uuid,
  'LIFE-MH-2024-000111',
  'LIFE',
  'CUST-IN-0009',
  'INSURED-IN-0009',
  'life',
  'IN-MH',
  'insured',
  0.00,
  10000000.00, -- ₹1 crore coverage
  0.00,
  '2022-01-01',
  '2047-01-01'
)
ON CONFLICT (policy_number) DO NOTHING;

INSERT INTO life_policy_profiles (policy_id, insured_age)
VALUES (
  '30000000-0000-0000-0000-000000000001'::uuid,
  28
)
ON CONFLICT (policy_id) DO NOTHING;

-- 10. Life - Middle-aged with long tenure
INSERT INTO policies (
  policy_id, policy_number, policy_type, customer_id, insured_id, product_line, region_code, asset_type,
  asset_value, coverage_limit, deductible, effective_date, expiry_date
)
VALUES (
  '30000000-0000-0000-0000-000000000002'::uuid,
  'LIFE-DL-2019-000222',
  'LIFE',
  'CUST-IN-0010',
  'INSURED-IN-0010',
  'life',
  'IN-DL',
  'insured',
  0.00,
  5000000.00, -- ₹50 lakh
  0.00,
  '2019-06-15',
  '2044-06-15'
)
ON CONFLICT (policy_number) DO NOTHING;

INSERT INTO life_policy_profiles (policy_id, insured_age)
VALUES (
  '30000000-0000-0000-0000-000000000002'::uuid,
  56
)
ON CONFLICT (policy_id) DO NOTHING;

-- ========================================
-- CLAIMS DATA (AUTO policies)
-- ========================================

-- Claims for AUTO-MH-2024-000341 (High risk - 4 claims in 36 months)
INSERT INTO claims (claim_id, policy_id, loss_date, reported_date, claim_type, status, paid_amount, reserve_amount, description)
VALUES
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000001'::uuid, '2024-10-15', '2024-10-16', 'collision', 'closed', 45000.00, 0.00, 'Front-end collision at traffic signal'),
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000001'::uuid, '2024-06-22', '2024-06-22', 'comprehensive', 'closed', 18000.00, 0.00, 'Side mirror damage - parking lot'),
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000001'::uuid, '2023-12-05', '2023-12-06', 'collision', 'closed', 62000.00, 0.00, 'Rear-end collision - highway'),
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000001'::uuid, '2023-08-18', '2023-08-19', 'comprehensive', 'closed', 12000.00, 0.00, 'Windshield crack')
ON CONFLICT DO NOTHING;

-- Claims for AUTO-DL-2024-000542 (Moderate - 2 claims)
INSERT INTO claims (claim_id, policy_id, loss_date, reported_date, claim_type, status, paid_amount, reserve_amount, description)
VALUES
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000002'::uuid, '2024-08-10', '2024-08-11', 'comprehensive', 'closed', 15000.00, 0.00, 'Hail damage to hood'),
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000002'::uuid, '2024-02-20', '2024-02-21', 'collision', 'closed', 28000.00, 0.00, 'Minor fender bender')
ON CONFLICT DO NOTHING;

-- Claims for AUTO-TN-2024-000678 (High frequency - 5 claims)
INSERT INTO claims (claim_id, policy_id, loss_date, reported_date, claim_type, status, paid_amount, reserve_amount, description)
VALUES
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000004'::uuid, '2024-11-05', '2024-11-05', 'comprehensive', 'open', 0.00, 25000.00, 'Flood damage - under assessment'),
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000004'::uuid, '2024-09-12', '2024-09-13', 'collision', 'closed', 38000.00, 0.00, 'T-bone collision at intersection'),
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000004'::uuid, '2024-05-18', '2024-05-19', 'comprehensive', 'closed', 8500.00, 0.00, 'Vandalism - keyed'),
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000004'::uuid, '2023-11-25', '2023-11-26', 'collision', 'closed', 52000.00, 0.00, 'Head-on collision - low speed'),
  (gen_random_uuid(), '10000000-0000-0000-0000-000000000004'::uuid, '2023-07-08', '2023-07-09', 'comprehensive', 'closed', 14000.00, 0.00, 'Broken taillight - hit and run')
ON CONFLICT DO NOTHING;

-- No claims for AUTO-KA-2024-001023 (Clean record - Bangalore)
-- No claims for AUTO-MH-2024-000892 (Clean record - Pune)

-- Claims for HLTH policies
INSERT INTO claims (claim_id, policy_id, loss_date, reported_date, claim_type, status, paid_amount, reserve_amount, description)
VALUES
  (gen_random_uuid(), '20000000-0000-0000-0000-000000000002'::uuid, '2024-08-15', '2024-08-16', 'hospitalization', 'closed', 125000.00, 0.00, 'Diabetes-related hospitalization - 5 days'),
  (gen_random_uuid(), '20000000-0000-0000-0000-000000000003'::uuid, '2024-10-10', '2024-10-12', 'hospitalization', 'closed', 285000.00, 0.00, 'Cardiac procedure - angioplasty'),
  (gen_random_uuid(), '20000000-0000-0000-0000-000000000003'::uuid, '2024-06-05', '2024-06-06', 'medical', 'closed', 45000.00, 0.00, 'Routine check-up and medication')
ON CONFLICT DO NOTHING;

-- ========================================
-- TELEMATICS DATA (AUTO policies only)
-- ========================================

-- Mumbai driver - High risk behavior
INSERT INTO telematics_aggregates (
  telematics_aggregate_id, policy_id, period_start, period_end,
  miles_driven, harsh_braking_events, speeding_events, distracted_driving_events,
  night_driving_pct, avg_speed_mph
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000001'::uuid,
  '2024-11-15',
  '2024-12-15',
  850.00,
  28, -- High harsh braking
  42, -- High speeding
  18, -- High distraction
  35.5, -- High night driving
  42.3
)
ON CONFLICT (policy_id, period_start, period_end) DO NOTHING;

-- Delhi driver - Moderate behavior
INSERT INTO telematics_aggregates (
  telematics_aggregate_id, policy_id, period_start, period_end,
  miles_driven, harsh_braking_events, speeding_events, distracted_driving_events,
  night_driving_pct, avg_speed_mph
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000002'::uuid,
  '2024-11-15',
  '2024-12-15',
  620.00,
  12, -- Moderate
  15, -- Moderate
  8, -- Moderate
  18.2, -- Moderate night driving
  35.8
)
ON CONFLICT (policy_id, period_start, period_end) DO NOTHING;

-- Bangalore driver - Low risk behavior (safe driver)
INSERT INTO telematics_aggregates (
  telematics_aggregate_id, policy_id, period_start, period_end,
  miles_driven, harsh_braking_events, speeding_events, distracted_driving_events,
  night_driving_pct, avg_speed_mph
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000003'::uuid,
  '2024-11-15',
  '2024-12-15',
  1120.00,
  4, -- Very low
  6, -- Very low
  2, -- Very low
  8.5, -- Low night driving
  32.1
)
ON CONFLICT (policy_id, period_start, period_end) DO NOTHING;

-- Chennai driver - Moderate-high
INSERT INTO telematics_aggregates (
  telematics_aggregate_id, policy_id, period_start, period_end,
  miles_driven, harsh_braking_events, speeding_events, distracted_driving_events,
  night_driving_pct, avg_speed_mph
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000004'::uuid,
  '2024-11-15',
  '2024-12-15',
  720.00,
  18,
  25,
  12,
  22.5,
  38.5
)
ON CONFLICT (policy_id, period_start, period_end) DO NOTHING;

-- Pune driver - Low risk
INSERT INTO telematics_aggregates (
  telematics_aggregate_id, policy_id, period_start, period_end,
  miles_driven, harsh_braking_events, speeding_events, distracted_driving_events,
  night_driving_pct, avg_speed_mph
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000005'::uuid,
  '2024-11-15',
  '2024-12-15',
  540.00,
  5,
  8,
  3,
  12.0,
  33.2
)
ON CONFLICT (policy_id, period_start, period_end) DO NOTHING;

-- ========================================
-- IoT ASSET METRICS (AUTO policies)
-- ========================================

-- Mumbai - Moderate health
INSERT INTO iot_asset_metrics (
  iot_asset_metric_id, policy_id, captured_at, device_id,
  health_score, battery_pct, anomaly_count, last_maintenance_date, fault_codes
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000001'::uuid,
  '2024-12-15 10:30:00+05:30',
  'IOT-MH-341',
  68,
  85,
  3,
  '2024-09-10',
  '{"brake_wear": "moderate", "tire_pressure": "low"}'::jsonb
)
ON CONFLICT DO NOTHING;

-- Delhi - Good health
INSERT INTO iot_asset_metrics (
  iot_asset_metric_id, policy_id, captured_at, device_id,
  health_score, battery_pct, anomaly_count, last_maintenance_date, fault_codes
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000002'::uuid,
  '2024-12-15 11:15:00+05:30',
  'IOT-DL-542',
  82,
  92,
  1,
  '2024-10-20',
  '{}'::jsonb
)
ON CONFLICT DO NOTHING;

-- Bangalore - Excellent health
INSERT INTO iot_asset_metrics (
  iot_asset_metric_id, policy_id, captured_at, device_id,
  health_score, battery_pct, anomaly_count, last_maintenance_date, fault_codes
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000003'::uuid,
  '2024-12-15 09:45:00+05:30',
  'IOT-KA-1023',
  93,
  95,
  0,
  '2024-11-05',
  '{}'::jsonb
)
ON CONFLICT DO NOTHING;

-- Chennai - Poor health
INSERT INTO iot_asset_metrics (
  iot_asset_metric_id, policy_id, captured_at, device_id,
  health_score, battery_pct, anomaly_count, last_maintenance_date, fault_codes
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000004'::uuid,
  '2024-12-15 14:20:00+05:30',
  'IOT-TN-678',
  52,
  78,
  7,
  '2024-04-15',
  '{"engine_warning": "active", "brake_wear": "high", "oil_level": "low"}'::jsonb
)
ON CONFLICT DO NOTHING;

-- Pune - Good health
INSERT INTO iot_asset_metrics (
  iot_asset_metric_id, policy_id, captured_at, device_id,
  health_score, battery_pct, anomaly_count, last_maintenance_date, fault_codes
)
VALUES (
  gen_random_uuid(),
  '10000000-0000-0000-0000-000000000005'::uuid,
  '2024-12-15 16:00:00+05:30',
  'IOT-MH-892',
  88,
  90,
  1,
  '2024-11-01',
  '{}'::jsonb
)
ON CONFLICT DO NOTHING;

-- ========================================
-- CLIMATE RISK INDICES (Indian Regions)
-- ========================================

INSERT INTO climate_risk_indices (climate_risk_index_id, region_code, peril_type, index_date, hazard_index, source)
VALUES
  -- Mumbai (MH) - High flood risk (monsoon flooding)
  (gen_random_uuid(), 'IN-MH', 'flood', '2024-12-01', 78, 'India Meteorological Department'),
  (gen_random_uuid(), 'IN-MH', 'heat', '2024-12-01', 65, 'India Meteorological Department'),
  
  -- Delhi (DL) - High heat, moderate flood
  (gen_random_uuid(), 'IN-DL', 'flood', '2024-12-01', 48, 'India Meteorological Department'),
  (gen_random_uuid(), 'IN-DL', 'heat', '2024-12-01', 82, 'India Meteorological Department'),
  
  -- Karnataka (KA) - Moderate all risks
  (gen_random_uuid(), 'IN-KA', 'flood', '2024-12-01', 42, 'India Meteorological Department'),
  (gen_random_uuid(), 'IN-KA', 'heat', '2024-12-01', 55, 'India Meteorological Department'),
  
  -- Tamil Nadu (TN) - High flood (coastal)
  (gen_random_uuid(), 'IN-TN', 'flood', '2024-12-01', 72, 'India Meteorological Department'),
  (gen_random_uuid(), 'IN-TN', 'heat', '2024-12-01', 70, 'India Meteorological Department')
ON CONFLICT (region_code, peril_type, index_date) DO NOTHING;

COMMIT;
