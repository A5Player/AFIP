# AFIP Regression Patch 1 — Dashboard Panel Registration

This patch restores six existing dashboard panels that were implemented by earlier milestones but were not registered in `DashboardUIRuntime`.

## Scope
- Regression fix only.
- No new feature.
- No trading-logic change.
- No intelligence-engine change.
- No execution enablement.

## Restored panel IDs
- `production_readiness_complete`
- `knowledge_intelligence_foundation`
- `pattern_knowledge_engine`
- `pattern_similarity_search`
- `pattern_clustering`
- `pattern_statistics`

## Safety state
- Execution: `LOCKED_SIMULATION_ONLY`
- Direct execution: `False`
- Live execution: `Disabled`
- Order status: `NO_ORDER_SENT`
