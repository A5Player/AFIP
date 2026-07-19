# AFIP Milestone T Pack 6

## Robustness, Walk-Forward Validation & Research Promotion Evidence Gate

Milestone T Pack 6 adds a deterministic research-only validation layer for exit-policy evidence produced by Packs 4 and 5.

## Scope

- chronological train / validation / forward windows
- explicit no-future-leakage enforcement
- temporal stability scoring
- validation and forward degradation measurement
- deterministic spread, slippage, volatility, liquidity, session, and gap stress scenarios
- resilience and robustness scoring
- research promotion evidence scoring
- human-approval requirement
- research quarantine integration
- append-only, checksum-chain verified datasets
- dashboard-ready research validation metadata

## Safety Contract

- Patch Only
- backward compatible
- production trading logic unchanged
- production runtime unchanged
- no MT5 order calls
- `LOCKED_SIMULATION_ONLY`
- all records remain `EXPERIMENTAL`
- all records remain `production_usable = false`
- automatic promotion is always disabled
- a passing gate creates only `PROMOTION_CANDIDATE_RESEARCH_ONLY`

## New Datasets

- `walk_forward_windows`
- `walk_forward_observations`
- `walk_forward_results`
- `robustness_scenarios`
- `robustness_results`
- `promotion_evidence_records`

## Validation

Expected after applying this patch:

- focused Pack 6 tests: `20 passed`
- Financial Naming: `PASS`
- Local Quality: `PASS`
- Full Regression: `2188 passed`

The build environment did not contain the MetaTrader5 package, so MT5 data validation used the existing simulation fallback. The target Windows machine should perform the real MT5 data check through the Pack script.
