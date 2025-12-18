# Deterministic Loss Risk Index (LRI) Model

This system provides **forward-looking** (scenario- and rule-driven) loss prevention analytics.
It is explicitly **not** ML-based: no training, no learning, no randomness.

## Outputs
- **Loss Risk Index (LRI)**: integer 0–100
- **Risk band**: `LOW`, `MEDIUM`, `HIGH`
- **Risk components**: bounded 0–100 per component with raw context in `details`
- **Fired rules** and **preventive actions**

## Determinism & Auditability
- Every score is computed using explicit thresholds and weights.
- Missing data uses deterministic defaults (currently `50` for missing telematics/IoT; climate uses `missing_hazard_index_default`).
- Rule evaluation uses a restricted condition language (`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`) over a stable context object.

## Model Structure
The source of truth is [backend/app/risk/rules/ruleset_v1.json](backend/app/risk/rules/ruleset_v1.json).

### Components (0–100 each)
1. **claims_history** (weight 0.35)
   - Frequency tiered by count in 36-month lookback
   - Severity tiered by `paid + reserved`
   - Blend: 55% frequency / 45% severity

2. **telematics_behavior** (weight 0.25)
   - Event rates per 100 miles: harsh braking, speeding, distracted driving
   - Night driving percent
   - Sub-weights: 25% braking / 35% speeding / 25% distracted / 15% night

3. **iot_asset_health** (weight 0.20)
   - Health score inverted into risk
   - Anomaly count tiered
   - Sub-weights: 70% health / 30% anomalies

4. **climate_hazard** (weight 0.15)
   - Directly uses hazard index (0–100) for region/peril

5. **policy_exposure** (weight 0.05)
   - Asset value tiered
   - Deductible ratio inverted into exposure risk (lower deductible → higher exposure)

### LRI Formula
Let component scores be $s_i \in [0,100]$ and weights be $w_i$.

$$
\text{LRI} = \mathrm{round}\left(\frac{\sum_i w_i s_i}{\sum_i w_i}\right)
$$

### Risk Bands
- LOW: 0–34
- MEDIUM: 35–69
- HIGH: 70–100

## Preventive Action Rules
Rules are defined in the same ruleset JSON and evaluated against a stable context:
- `risk.lri`, `risk.band`
- `components.<name>.normalized_score`
- `inputs.<source>.<field>`

Initial rules:
- R-001: High risk coaching
- R-002: Asset inspection
- R-003: Climate mitigation checklist
- R-004: Claims review
