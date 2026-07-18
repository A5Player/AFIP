# AFIP Data Architecture V1

AFIP uses one central, profile-independent research dataset. P1-P4 are consumers of shared evidence and may apply different operational policies, but they must not create separate research truth.

## Layers

1. **Raw** — append-only observations exactly as received, with source and timestamps.
2. **Normalized** — units, symbols, time zones, and schemas standardized without destroying raw values.
3. **Derived** — indicators, classifications, patterns, scores, and cross-market context.
4. **Decision** — committed action, gates, sizing, execution permission, and complete trace.
5. **Outcome** — execution result and post-decision path measurements at M30/H1/H4/D1 or registered horizons.
6. **Knowledge** — aggregated evidence, rankings, stability, and formula-version-aware research conclusions.

## Non-negotiable rules

- Raw records are immutable and append-only.
- Every derived value records lineage and formula version.
- Every decision records all component scores and hard gates.
- Scores never override safety gates.
- Research eligibility travels with every observation/trade.
- Incident and configuration-error periods are quarantined, not deleted.
- Blind-forward research may only access information available at the simulated timestamp.
- Historical results are never silently recalculated in place; recomputation creates a new derived version.
