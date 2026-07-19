
## Milestone S Pack 6.1 — Knowledge Validation & Promotion Pipeline
- Cross-period and cross-regime validation of Pack 6.0 candidate knowledge.
- Deterministic research promotion decision and evidence traceability.
- Highest automatic state: RESEARCH_REVIEW_READY.
- Execution authority and automatic trading-policy changes remain prohibited.


## Milestone S Pack 6.2 â€” Knowledge Certification Framework

- Added research-only certification governance with deterministic IDs.
- Added central persistent data structure under `data/knowledge/certification/`.
- Added append-only registry/lineage/version/report/archive layout.
- Added schema metadata, data dictionary, migration guide, and user/technical/research guides.
- `execution_authority = NONE`; promotion to execution and automatic strategy changes remain prohibited.



## Milestone S Pack 6.3 - Knowledge Portability, Recovery & Reuse Framework
Added content-addressed manifests, SHA-256 verification, portable export bundles, verify-only import, isolated recovery, central data directories, data dictionary, migration guidance, and recovery runbook. Execution authority remains NONE and promotion to execution remains PROHIBITED.


## Milestone S Pack 6.4 - Knowledge Integrity Monitoring & Audit Framework

Added deterministic research-only integrity audits, append-only audit ledgers, metadata/guide/lineage checks,
quarantine recommendations, recovery runbook, data dictionary, and central governance storage under
`data/governance/integrity/`. Execution authority remains NONE and automatic repair is prohibited.


## Milestone S Pack 6.5 - Central Data Catalog & Dataset Registry

Added a profile-independent central catalog for datasets under `data/`, including stable IDs,
schema versions, storage paths, owners, producers, classifications, lifecycle states, retention,
lineage, guides, tags, discovery, validation, and deterministic snapshots. Execution authority remains NONE.


## Milestone S Pack 6.6 - Data Quality Scoring & Research Readiness Framework

Added deterministic quality scoring across completeness, consistency, validity, freshness, lineage,
documentation, and integrity. Added readiness levels, research-use restrictions, append-only assessment
ledgers, guides, data dictionary, and central storage under `data/governance/quality/`.
Execution authority remains NONE and automatic dataset promotion is prohibited.


## Milestone S Pack 6.7 - Long-Term Archive & Retention Policy

Added recommendation-only retention governance, legal hold, archive tiers, ledgers, and recovery guidance.


## Milestone S Pack 6.8 - Research Reproduction & Experiment Replay

Added deterministic experiment specifications, replay fingerprints, missing-dataset blocking, and offline-only manifests.


## Milestone S Pack 6.9 - Dataset Usage Ledger & Evidence Traceability

Added append-only usage events, research readiness enforcement, evidence references, and experiment linkage.


## Milestone S Pack 7.0 - Data Foundation Integration & Final Certification

Integrated all Data Foundation governance layers and added deterministic final research-foundation certification.


## Milestone S Pack 7.3 — Deterministic Position Capacity Formula

- Replaced P1-P3 expanded capital-tier configuration arrays with compact deterministic formulas.
- Preserved `CAPITAL_TIER_TABLE` runtime semantics by expanding formulas during profile policy loading.
- Preserved support for explicit legacy capital-tier arrays.
- Added full-curve equivalence regression coverage for P1, P2, and P3.
- No trading decision, protection, execution, TP, SL, or spread policy changed.

## Milestone T Pack 1 — Research Quarantine & Knowledge Promotion Foundation

Status: PATCH DELIVERED

- Experimental research is isolated from production-approved knowledge.
- Production readers fail closed and accept only verified `PRODUCTION_APPROVED` records.
- Research promotion requires sample size, out-of-sample, walk-forward, profit factor, positive expectancy, drawdown limit, chronological replay, data quality, no future leakage, and approval evidence.
- TOP10/TOP100 ranking is disabled.
- Future approved-candidate selection will use current-market context with lower drawdown, higher net profit, and higher win probability.
- No trading or execution behavior changed.


## Milestone T Pack 2 — Chronological Replay & Position Management Research Foundation

Status: Implemented and locally validated.

Capabilities:
- Strict chronological replay with no-future-data decision contexts.
- Flexible one-to-three-leg position-management research plans.
- MFE/MAE and final path outcome measurement.
- Decision alternatives for hold, close, partial close, break-even, trailing, pyramid, and no-pyramid.
- Dynamic pyramid research requires profit, reduced existing risk, supportive regime/structure/trend, and total-risk compliance.
- Overnight holding alone never authorizes a pyramid add.
- Research records remain EXPERIMENTAL and isolated from production execution.

Production impact:
- No production trading-logic change.
- No MT5 order send or position modification.
- No lot-size, TP, or SL change.


## Milestone T Pack 3 — Historical Replay Runner & Research Dataset Builder

Status: IMPLEMENTED AND VALIDATED

### Purpose

Provide a deterministic research-only runner that walks historical market candles one bar at a time without future exposure and builds append-only experimental datasets for later entry, exit, position-management, loss-control, and pyramid research.

### Components

- `afip/historical_replay_research/runtime.py`
- `afip/historical_replay_research/__init__.py`
- `tests/test_milestone_t_pack_3_historical_replay_runner.py`

### Research Datasets

- snapshots
- candidates
- decisions
- timeline
- run summaries

Each dataset is JSONL, append-only, sequence-numbered, and protected by a previous-checksum chain. All generated research records use state `EXPERIMENTAL` and remain unavailable to Production Runtime.

### Replay Guarantees

- unique strictly increasing timestamps
- one-bar-at-a-time execution
- snapshot provider receives visible candles only
- no future candle is included in decision context
- deterministic replay clock
- resumable processing from the latest `BAR_PROCESSED` event
- dataset tampering is detectable

### Production Boundary

No MT5 order check, order send, position modification, production lot sizing, TP, SL, or trading-decision behavior is changed by this pack.

### Validation

- Focused tests: 16 passed
- Financial Naming: PASS
- Full regression: 2131 passed


## Milestone T Pack 4 — Exit, Loss-Control & Position Outcome Research Engine

Status: PATCH DELIVERED

- Added research-only exit and loss-control policy evaluation.
- Added dynamic profit-target, stop-loss, break-even, trailing-stop, and maximum-holding alternatives.
- Added position lifecycle, exit alternative, position outcome, and exit quality append-only datasets.
- Added outcome classification, MFE/MAE, profit capture, missed profit, avoided loss, capital preservation, and exit quality metrics.
- Same-bar stop/target ambiguity uses a conservative stop-first assumption.
- All records remain `EXPERIMENTAL`, `production_usable=false`, and protected by Research Quarantine.
- No MT5 order, Production Runtime, position sizing, TP, SL, or trading logic changed.


## Milestone T Pack 5 — Exit Experiment Aggregation, Context Segmentation & Evidence Evaluation

### Architecture

- Adds a research-only evidence layer above Pack 4 position outcomes.
- Aggregates outcomes by exit policy and deterministic market-context segment.
- Records sample size, win rate, average/median/worst/best realized R, dispersion, exit quality, capital preservation, profit capture, adverse excursion, holding period, consistency, and evidence score.
- Evaluates research evidence eligibility without Production promotion.
- Compares policies only within a shared context segment and never selects a winner.

### Research Datasets

- `exit_evidence_observations`
- `exit_context_segments`
- `exit_evidence_summaries`
- `exit_evidence_evaluations`
- `exit_policy_comparisons`

### Safety

- Research state remains `EXPERIMENTAL`.
- Production usability remains false.
- Automatic promotion is prohibited.
- Production Runtime and Trading Logic are unchanged.
- No MT5 execution action is present.




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



## Milestone T Pack 8 — Runtime Standard Adapter & Historical Backfill Orchestration

- ACTIVE research-derived standards can produce context-specific runtime guidance.
- Guidance includes entry confidence adjustment, units, lot per unit, SL, TP, break-even, trailing, hold, and close policies.
- Existing risk, trading-cost, capacity, and execution permission gates remain mandatory.
- Historical backfill is earliest-available to latest-closed, deduplicated, provenance-preserving, and append-only.
- No MT5 order sender or automatic execution authorization is added.




## Milestone T Pack 9 — MT5 Historical Provider, Resumable Backfill, Decision Trace Wiring & Dashboard Data Contract Foundation

Status: COMPLETE

Added:
- `afip.mt5_historical_integration`
- broker symbol resolution
- resumable historical backfill checkpoints
- provider run evidence and runtime decision traces
- dashboard research rankings

Dashboard architecture decision:
- Page 1 Operations: P1-P4 together without vertical scrolling as the design target; refresh every 5-10 seconds, default 5 seconds.
- Page 2 Intelligence/Engine: manual refresh, preserve scroll position, Top 10 visible and Top 100 expandable by graph pattern and market situation.
- All unshown research records remain stored; dashboard reports the count beyond Top 100.

Execution remains governed by existing safety gates. No order sender was added.



## Milestone T Pack 10 - Adaptive Multi-Objective Plan Ranking

Status: Completed

Architecture added:

- Capital Preservation Gate
- Evidence Reliability Gate
- Context-aware bounded weight adaptation
- Profile-specific ranking weights for P1-P4
- Conservative win-rate and risk-adjusted performance selection
- Deterministic Top 10 and Top 100 dashboard ranking records
- Append-only adaptive_plan_rankings dataset

Locked policy:

AFIP does not select the highest-profit plan. AFIP selects the most reliable, capital-preserving, context-appropriate and risk-adjusted plan. Profit is an outcome, not the first selection criterion.

Runtime execution permission remains outside this module.



## Milestone T Pack 11 — Complete Trade Plan and Capital Stewardship

Status: FOUNDATION COMPLETE

Added:
- CompleteTradePlan
- MarketSituationPlan
- EntryPlan
- CapitalManagementPlan
- PositionCarePlan
- ExitPlan
- FailureRecoveryPlan
- CompleteTradePlanCertifier
- TradePlanLifecycleRecorder
- TradePlanDashboardContract

Permanent policy:
- NO_COMPLETE_PLAN_NO_ORDER
- Capital stewardship has authority over requested units
- Confidence cannot determine position quantity
- Recovery reconciliation is mandatory after restart
- Unknown or incomplete state blocks new risk

Datasets:
- complete_trade_plans
- trade_plan_certifications
- trade_plan_lifecycle_events

Execution remains LOCKED_SIMULATION_ONLY.
