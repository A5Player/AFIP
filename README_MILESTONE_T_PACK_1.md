# AFIP Milestone T Pack 1
## Research Quarantine & Knowledge Promotion Foundation

This patch establishes a fail-closed boundary between experimental research and production-approved knowledge.

## Core guarantees

- Experimental research is physically and logically separate from production-approved knowledge.
- Production can read only `PRODUCTION_APPROVED` records with a verified promotion checksum.
- Experimental, pending, rejected, candidate, approved, and revoked records have explicit lifecycle states.
- Missing evidence always blocks promotion.
- High profit or high win rate can never override excessive drawdown, weak validation, poor data quality, or future leakage.
- TOP10 and TOP100 ranking are not used.
- Approved knowledge is later compared by current-market suitability using lower drawdown, higher net profit, and higher win probability.
- No trading logic, profile policy, position sizing, execution permission, TP, or SL behavior is changed by this pack.

## Promotion flow

`EXPERIMENTAL -> VALIDATION_PENDING -> APPROVED_CANDIDATE -> PRODUCTION_APPROVED`

`REJECTED` and `REVOKED` records are never production-readable.

## Minimum evidence defaults

- Total sample size: at least 300 trades
- Out-of-sample size: at least 100 trades
- Walk-forward windows: at least 3
- Profit factor: at least 1.20
- Expectancy: positive
- Maximum drawdown: no more than 20%
- Chronological replay: verified
- Future leakage: none
- Data quality: certified
- Manual approval and approver identity: required

The thresholds are stored in `config/research_promotion_policy.json` and are not hardcoded into trading execution.

## Dashboard foundation

The research governance snapshot reports:

- Research quarantine status
- Fail-closed production status
- Counts by lifecycle state
- Number of production-usable knowledge records
- Confirmation that experimental data is not used by production
- Selection objectives: lower drawdown, higher net profit, higher win probability
- Confirmation that TOP ranking is disabled
