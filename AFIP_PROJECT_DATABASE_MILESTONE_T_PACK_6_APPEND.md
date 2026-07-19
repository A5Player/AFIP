
## Milestone T Pack 6 — Robustness, Walk-Forward Validation & Research Promotion Evidence Gate

Status: COMPLETE

Pack 6 introduces `afip.research_validation`, a research-only validation layer that consumes chronological quarantined observations and produces deterministic walk-forward, robustness, and promotion-evidence records.

Capabilities:

- chronological Train / Validation / Forward separation
- explicit non-overlapping indexes and no-future-leakage status
- temporal stability and degradation metrics
- deterministic transaction-cost and market-condition stress penalties
- robustness and resilience scoring
- evidence sufficiency evaluation
- human approval requirement
- no automatic policy selection or promotion
- dashboard-ready validation metadata

New append-only datasets:

- walk_forward_windows
- walk_forward_observations
- walk_forward_results
- robustness_scenarios
- robustness_results
- promotion_evidence_records

Production contract:

- Runtime unchanged
- Trading logic unchanged
- No MT5 order execution
- LOCKED_SIMULATION_ONLY
- research_state = EXPERIMENTAL
- production_usable = false
- automatic_promotion_allowed = false

Validation baseline: 20 focused tests; 2188 full tests passed.
