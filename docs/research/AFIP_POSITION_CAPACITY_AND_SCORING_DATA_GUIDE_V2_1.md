# AFIP Position Capacity and Scoring Data Guide V2.1

## Purpose
This guide defines the authoritative meaning, origin, use, and research value of every field used to choose AFIP position units and lot capacity. It is designed for audit, dataset reuse, model comparison, and future AFIP versions.

## Decision layers
1. **Intelligence request** proposes the number of units justified by current evidence.
2. **Confidence ceiling** limits units to 0, 1, 2, or 3.
3. **Balance tier** limits available unit slots and maximum lot size per unit.
4. **Profile policy** defines growth speed and absolute lot ceiling.
5. **Risk, margin, cost, duplicate-signal, and execution gates** may reduce the result further or block it.
6. **Execution result** records what was actually sent and accepted by MT5.

A ceiling is never an automatic target.

## Confidence scoring
| Confidence | Maximum units | Meaning |
|---|---:|---|
| below 98.00 | 0 | signal is not eligible |
| 98.00–98.49 | 1 | one-unit ceiling |
| 98.50–99.49 | 2 | two-unit ceiling |
| 99.50–100.00 | 3 | three-unit ceiling |

### Score origin
The confidence value comes from the certified decision/intelligence output for the signal. Store the producing module, version, timestamp, market snapshot identifier, component scores, weights, normalization method, missing inputs, and final confidence. Never store only the final number when component evidence is available.

### Score use
Confidence is used only as a maximum-unit ceiling. It must not automatically request or fill that number of units.

## Balance capacity fields
- `minimum_balance`: lowest account balance eligible for the tier.
- `lots`: maximum available lot capacity for each unit slot at that tier.
- `maximum_lot_per_order`: profile hard ceiling per unit.
- `maximum_concurrent_orders`: profile-wide order ceiling; zero is reserved for the P4 research policy where explicitly documented.

Balance tiers use account balance reported by the execution account snapshot before allocation. Store currency, broker, server, account identifier, timestamp, equity, free margin, and open-order count beside the selected tier.

## Profile policies
### P1 — High Safety
- Below 300: capacity 1 × 0.01.
- From 300: capacity 2 × 0.01.
- From 900: capacity 3 × 0.01.
- From 1,800: 3 × 0.02, increasing by the certified staircase.
- Absolute ceiling: 3 × 0.10.

### P2 — Balanced
- Same capacity staircase as P1 through 3 × 0.10 at balance 19,800.
- Continues on the same increasing-balance staircase to 3 × 1.00.
- Absolute ceiling: 3 × 1.00.

### P3 — High Risk Within Plan
- Below 200: capacity 1 × 0.01.
- From 200: capacity 2 × 0.01.
- From 450: capacity 3 × 0.01.
- From 1,200: 3 × 0.02.
- Thereafter each additional 600 balance raises maximum lot per unit by 0.01.
- Absolute ceiling: 3 × 10.00.

### P4 — Research
- Fixed 0.01 lot per unit.
- No lot-size growth.
- Research unit accumulation is not limited by the P1–P3 growth tables.
- Every research unit must preserve its own strategy, TP, SL, hypothesis, market state, and outcome identifiers.

## Required audit record
For every allocation decision store at minimum:
- decision and signal identifiers;
- profile and policy version;
- market timestamp and data snapshot identifiers;
- intelligence-requested units and reason;
- confidence value, component scores, source modules, and confidence ceiling;
- account balance/equity/free margin and selected balance tier;
- balance capacity slots and lot per slot;
- risk, margin, trading-cost, duplicate, and execution gate results;
- approved units and lots before order send;
- MT5 check/send request and result codes;
- TP/SL plan identifier and per-unit protection values;
- reduction/block reasons at every layer;
- software commit, config checksum, and dataset schema version.

## Research and future-version use
Use these records to compare requested versus approved versus executed units, evaluate each gate, recalibrate confidence bands, test alternative balance curves, reproduce historical decisions, and train future versions. Research must group data by market attributes, pattern family, regime, strategy, protection plan, and policy version rather than binding evidence permanently to P1–P4 names.

## Data quality rules
- Preserve raw source observations and derived scores separately.
- Never overwrite a historical policy version or score explanation.
- Mark simulated, demo, live, rejected, and anomalous records explicitly.
- Exclude known faulty execution periods from performance certification while retaining them for defect research.
- Record units, currencies, point size, digits, spread units, and timezone explicitly.
- Every derived field must identify its source fields and calculation version.
