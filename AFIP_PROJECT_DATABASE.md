
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

