# AFIP Milestone T Pack 5

## Exit Experiment Aggregation, Context Segmentation & Evidence Evaluation

This patch adds a research-only evidence layer above Milestone T Pack 4 position outcomes.

### Added

- deterministic exit evidence observations
- market-context segmentation
- policy-and-context aggregation
- expectancy, dispersion, consistency, exit-quality, and capital-preservation metrics
- research evidence eligibility evaluation
- pairwise policy comparison without winner selection
- append-only evidence datasets and checksum-chain verification
- research quarantine metadata

### Context Dimensions

- market regime
- market structure
- liquidity state
- trend state
- volatility state
- trading session
- direction
- pattern family

### Safety Boundary

- Research state: `EXPERIMENTAL`
- Production usable: `false`
- Automatic promotion: prohibited
- MT5 order/check/send/modify/close: none
- Production Runtime: unchanged
- Production Trading Logic: unchanged

### Validation

Run `RUN_MILESTONE_T_PACK_5.ps1` or `RUN_MILESTONE_T_PACK_5.bat`.
