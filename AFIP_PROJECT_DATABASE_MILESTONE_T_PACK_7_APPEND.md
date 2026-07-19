
## Milestone T Pack 7 — Research-Derived Initial Standard

Owner decision: validated research evidence may become the operating initial standard without a second waiting cycle.

Implemented:
- versioned initial-standard registry
- owner approval and evidence lineage
- deterministic context selection
- highest-evidence matched policy selection
- supersession history
- maximum-history cross-market coverage plan
- append-only datasets: research_standard_versions, research_standard_selections, historical_coverage_plans

Safety boundary:
- approved standards may be production_usable
- no MT5 order sender added
- automatic order execution cannot be authorized by this registry
- existing safety and execution gates remain authoritative

Validation: 24 focused tests; 2212 full regression tests.
