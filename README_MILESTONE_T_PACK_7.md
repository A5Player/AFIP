# AFIP Milestone T Pack 7

## Research-Derived Initial Standard, Context Selection & Historical Coverage Foundation

This pack implements the owner decision that validated research evidence is itself proof and may become the initial operating standard without an additional waiting cycle.

## Capabilities

- Versioned research-derived initial standards
- Explicit owner approval record
- Complete evidence and dataset lineage
- Deterministic context matching
- Highest-evidence policy selection inside the matching context
- Standard supersession and rollback-ready history
- Production-usable standard manifest
- Maximum-history coverage planning
- Cross-market context requests for GOLD, USD, FX majors, oil, and equity indices
- Multi-timeframe coverage from M1 through D1
- Append-only standard, selection, and coverage datasets

## Important boundary

The registry may mark an approved standard `production_usable = true`. It does not send an order and cannot authorize automatic order execution. Existing Risk, Trading Cost, Position Sizing, Execution Permission, Demo Gateway, and MT5 order controls remain authoritative.

## Baseline

- Required preceding commit: `89d20bfa26746bab87507e179633f0dff52f7eb4`
- Pack 6 regression baseline: 2188 passed
- Pack 7 focused tests: 24 passed
- Pack 7 full regression: 2212 passed
- Runtime: LOCKED_SIMULATION_ONLY
