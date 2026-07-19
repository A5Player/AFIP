
## Latest: Milestone S Pack 6.1
Knowledge Validation & Promotion Pipeline added. Apply as Patch Only, run focused tests and full regression. `RESEARCH_REVIEW_READY` requires human approval and does not authorize execution.


## Milestone S Pack 6.2 Handoff

Pack 6.2 adds the research-only Knowledge Certification Framework. Validated Pack 6.1 evidence can become `RESEARCH_CERTIFIED` only after sample, period, regime, stability, validation, drift, and human-review gates pass. All persistent outputs belong under `data/knowledge/certification/`. No broker, MT5, order, profile, lot-size, TP, SL, or execution policy is changed.



## Milestone S Pack 6.3 Handoff
Pack 6.3 adds research-data portability and recovery. Import defaults to verification only and applied imports use isolated bundle-ID directories. Original datasets and bundles are never silently overwritten. No trading, broker, profile, TP, SL, lot, or risk authority was added.


## Milestone S Pack 6.4 Handoff

Pack 6.4 adds knowledge/data integrity monitoring. Apply documentation updates once, run focused and full
regression tests, and keep runtime dashboard artifacts out of Git unless intentionally updated.


## Milestone S Pack 6.5 Handoff

Pack 6.5 adds the central dataset catalog. Apply documentation updates once, run focused and full
regression tests, and do not stage generated dashboard HTML unless intentionally changed.


## Milestone S Pack 6.6 Handoff

Pack 6.6 adds data quality scoring and research-readiness classification. Apply documentation updates,
run focused and full regression tests, and keep generated dashboard HTML unstaged unless intentionally changed.


## Milestone S Pack 6.7 Handoff

Run focused/full tests. No automatic deletion is permitted.


## Milestone S Pack 6.8 Handoff

Replay is offline research only and cannot execute trades.


## Milestone S Pack 6.9 Handoff

Record dataset usage before research consumption; no execution authority.


## Milestone S Pack 7.0 Handoff

All eight checks must pass. Certification remains research-only and cannot alter execution.


## Latest verified development: Milestone S Pack 7.3

Position-capacity configuration for P1-P3 is now stored as deterministic formulas and expanded into the legacy in-memory tier table at policy load time. Runtime allocation mode and Capital Growth Engine behavior remain unchanged. Legacy explicit tables remain supported. Validate with `RUN_MILESTONE_S_PACK_7_3.ps1`, full pytest, and AFIP local quality check before commit.

## Milestone T Pack 1 Handoff

Pack: Research Quarantine & Knowledge Promotion Foundation

Important status separation:

- Policy agreed: YES
- Patch files created: YES
- User local focused tests: PENDING
- User local full regression: PENDING
- Git commit/push: PENDING

Production knowledge rule:

- Research data remains quarantined until every promotion gate passes.
- Production runtime must read only verified `PRODUCTION_APPROVED` knowledge.
- TOP10/TOP100 is not part of the selection design.
- Selection objectives are lower drawdown, higher net profit, and higher win probability under matching market context.


## Milestone T Pack 2 Handoff

Milestone T Pack 2 introduces the research-only chronological replay and position-management foundation. It supports 1-3 flexible legs, MFE/MAE analysis, post-exit observation, alternative-decision recording, and conditional pyramid research. Results are quarantined as EXPERIMENTAL and cannot influence production until later validation and promotion.

Recommended next pack:
- Exit Policy Experiment Registry
- TP/SL/Trailing/Break-even scenario generation
- Per-context outcome aggregation
- Survival-first objective evaluation emphasizing drawdown and capital preservation


## Milestone T Pack 3 Handoff

### Completed

Historical Replay Runner & Research Dataset Builder is implemented as a research-only module.

### Verified Baseline

- Source baseline commit: `1aede17`
- Pack 3 focused tests: 16 passed
- Financial Naming: PASS
- Full regression after Pack 3: 2131 passed

### Architectural Decisions Preserved

- No TOP10 or TOP100 production ranking
- Research must pass governance before production visibility
- Historical replay must not see future candles
- One, two, or three position legs are optional research choices, not mandatory fixed stages
- Overnight holding does not automatically authorize a pyramid addition
- Capital survival and loss control remain higher-priority research objectives than maximum profit
- Research datasets are profile-independent and market-context classified
- All Pack 3 output remains `EXPERIMENTAL`

### Pack 3 Output

- deterministic chronological runner
- replay clock
- market snapshot provider interface
- research candidate provider interface
- append-only snapshot, candidate, decision, timeline, and summary datasets
- checksum chain verification
- tamper detection
- replay resume
- research dashboard metadata

### Not Yet Implemented

Pack 3 does not optimize entry, exit, stop placement, profit targets, holding duration, or pyramid additions. These belong to later Milestone T packs and must consume the Pack 3 datasets without weakening Research Quarantine.

### Recommended Next Pack

Milestone T Pack 4 — Exit, Loss-Control & Position Outcome Research Engine.

Recommended priorities:

1. capital survival and controlled loss
2. early invalidation and safe exit
3. partial exit and full exit alternatives
4. hold and trailing alternatives
5. missed-profit and avoided-loss measurement
6. post-exit M30/H1/H4/D1 observation


## Milestone T Pack 4 Handoff

### Completed

Exit, Loss-Control & Position Outcome Research Engine is implemented as a research-only module.

### Source Baseline

- User ZIP baseline commit: `697ef2e51fc3ffcd4fd985803ecc5050ebf8cf65`

### Pack 4 Output

- exit policy model
- hypothetical position research case
- bar-by-bar exit outcome engine
- dynamic TP and SL alternatives
- break-even and trailing alternatives
- maximum holding-period alternative
- conservative same-bar ambiguity handling
- position lifecycle dataset
- exit alternative dataset
- position outcome dataset
- exit quality dataset
- capital preservation and exit quality scoring
- multi-policy experiment runner without production selection

### Architectural Boundary

- Research state remains `EXPERIMENTAL`.
- Production usability remains false.
- No MT5 order check/send/modify/close.
- No Production Trading Logic change.
- No automatic research promotion.

### Recommended Next Pack

Milestone T Pack 5 — Exit Experiment Aggregation, Context Segmentation & Evidence Evaluation.


## Milestone T Pack 5 Handoff

### Completed

Exit Experiment Aggregation, Context Segmentation & Evidence Evaluation is implemented as a research-only module.

### Source Baseline

- User repository commit after Pack 4: `807a9d07cc00493a22d468d8dee53a52a6bc34bb`

### Pack 5 Output

- deterministic evidence observation model
- eight-dimensional market context segment
- policy/context evidence aggregation
- expectancy and dispersion metrics
- consistency and evidence scoring
- research evidence eligibility
- policy pair comparison without winner selection
- append-only evidence datasets
- research quarantine and no-auto-promotion controls

### Architectural Boundary

- Research state remains `EXPERIMENTAL`.
- Production usability remains false.
- No MT5 order check/send/modify/close.
- No Production Runtime or Trading Logic change.
- No automatic policy selection or promotion.

### Recommended Next Pack

Milestone T Pack 6 — Robustness, Walk-Forward Validation & Research Promotion Evidence Gate.




# Milestone T Pack 7 Handoff

## Completed

Research-Derived Initial Standard, Context Selection & Historical Coverage Foundation.

## Owner policy decision

Research that has passed the established evidence pipeline is considered proven enough to become the initial operating standard. Do not add another passive waiting cycle before use.

## Current verified baseline

- Focused Pack 7: 24 passed
- Full Regression: 2212 passed
- Financial Naming: PASS
- Local Quality: PASS
- Runtime during validation: LOCKED_SIMULATION_ONLY
- MT5 Order Sender: UNCHANGED

## New module

`afip/research_standardization/`

## Next pack

Milestone T Pack 8 — Runtime Standard Adapter, Historical Backfill Orchestration & Context-Aware Decision/Position Management Integration.

Pack 8 should connect ACTIVE research-derived standards to the existing decision and position-management inputs without bypassing any safety or execution gate. It should also orchestrate earliest-available historical collection using broker/source capability and record actual coverage gaps.




## Latest Completed — Milestone T Pack 9

Title: MT5 Historical Provider, Resumable Backfill, Decision Trace Wiring & Dashboard Data Contract Foundation

Validation baseline after Pack 8: 2222 passed
Pack 9 focused tests: 14 passed
Expected full regression: 2236 passed
Financial Naming: PASS
Local Quality: PASS
Execution: LOCKED_SIMULATION_ONLY in validation environment
MT5 order execution: unchanged

Dashboard requirements locked:
- Operations page: P1-P4 combined, five-to-ten-second refresh, no-scroll target.
- Intelligence page: manual refresh with preserved scroll.
- Top 10 visible; Top 100 expandable for pattern and situation rankings.
- Keep and count all underlying research data even when not displayed.

Next target:
Milestone T Pack 10 — Real MT5 Gateway Adapter, Multi-Instrument Historical Backfill Runner, Profile Operations Snapshot & Dashboard Read Model Foundation.



# Handoff — Milestone T Pack 11

Latest completed foundation:
Complete Trade Plan Contract, Capital Stewardship Authority, Entry-Care-Exit Lifecycle, Failure Recovery Plan and Dashboard Contract.

Validation target:
- Focused tests: 16 passed
- Financial Naming: PASS
- Local Quality: PASS
- Expected full regression after installation: previous 2252 + 16 = 2268 passed

Next recommended pack:
Milestone T Pack 12 — Plan-to-Ranking Wiring, Runtime Decision Trace Integration, Capital Capacity Snapshot and Recovery Reconciliation Read Model.

## Latest Completed - Milestone T Pack 12

Certified Trade Plan Runtime Orchestration is complete.

Current regression baseline: 2284 passed.

Current authority chain:

Research Ranking -> Complete Trade Plan -> Certification -> Runtime Capital Capacity -> Recovery Reconciliation -> READY_FOR_EXECUTION_GATE_REVIEW -> Existing Execution Gates.

Pack 12 never grants execution permission and never sends MT5 orders.

Recommended next pack:

Milestone T Pack 13 - Position Care Runtime State, Exit Plan Supervision, Profit Protection Decision Trace, and Unattended Watchdog Read Model.



## Milestone T Pack 14 Handoff

Pack 14 establishes unattended continuity and recovery supervision. A restart or interruption does not grant authority to continue automatically until account state, market data, open positions, ledger positions, pending position changes, equity state, drawdown state and duplicate prevention are reconciled. Unknown, missing or manual positions cause a safe operating state. No MT5 order authority was added.

## Milestone T Final Handoff

Milestone T closes after Pack 15 validation. The foundation now covers complete trade plans, runtime capital capacity, position care and exit supervision, unattended continuity, restart reconciliation, recovery supervision, and production evidence certification.

Execution remains locked. No MT5 send, modification, or close authority was added by Packs 11–15. Continue only with Patch Only, backward-compatible work and preserve all existing execution gates.


## Phase U Pack 1 Handoff
Run focused tests, Financial Naming, full pytest, Local Quality, then rebuild Dashboard with `python -m afip.dashboard_ui`. Next work must wire FOUNDATION_ONLY components into the primary runtime one at a time.

## Phase U Pack 1.1 Handoff

Dashboard compatibility regression corrected. Legacy Milestone H Pack 9 and Pack 10 title markers remain available in generated HTML while the Phase U dashboard remains the visible primary interface.

## Phase U Pack 3 Handoff
Run `python -m afip.dashboard_ui` to generate three separate dashboards.
Financial values must come from P1-P4/MT5 runtime sources. No sample financial values are permitted.
Research ranking is derived from readable JSON/JSONL records under runtime/research, data/research and data/knowledge. Empty categories must show DATA_UNAVAILABLE.


## Phase U Pack 3.3.1 Handoff — Universal Timeframe Registry
- Canonical ordered timeframes: M1, M5, M15, M30, H1, H4, D1.
- Historical collection and automatic chronological replay now consume the central registry.
- TimeframeAdapter remains backward compatible and delegates conversion to the registry.
- No trading, risk, lot sizing, SL, TP or execution policy was changed.
- Historical and research storage remain append-only.
- M5 1,441/2,000 replay coverage remains unresolved pending source/runtime evidence certification.


## Phase U Pack 3.3.2 Handoff
M30 historical collection is persisted in the append-only financial data lake. Next work: M30 gap detection/backfill/integrity and evidence-based M5 replay coverage investigation. Real-account readiness remains unclaimed.

## Phase U Pack 3.3.3 Handoff

Status after validation: M30 chronological replay and exact-window coverage evidence available.

Important investigation result: the former M5 1,441 processed count is explained by a 559 next-index checkpoint continuation. Because the legacy replay ID did not bind that checkpoint to first/last timestamps, it was not sufficient evidence of full coverage for the newly downloaded 2,000-bar MT5 window. Pack 3.3.3 preserves the legacy data and starts an append-only exact-window generation.

Safety: Live execution policy remains unchanged and disabled by this research pack.

## Phase U Pack 3.3.4 Handoff — M30 Data Quality and Automatic Backfill

- Universal registered timeframe quality evidence now covers M1, M5, M15, M30, H1, H4, and D1.
- Automatic Research Status exposes integrity, duplicate, gap, missing-bar, freshness, and backfill evidence.
- Backfill merging preserves existing records and accepted new bars remain append-only.
- MT5 backfill is research-only and does not call order_send.
- No live trading policy or financial risk-control setting was changed.

## Phase U Pack 3.3.5 Handoff — Dashboard Timeframe Research Status

Dashboard 3 now renders structured status evidence for all seven registered timeframes, including M30. It reads `runtime/research/automatic_research_status.json` and visibly reports missing evidence as `NOT_RECORDED` or `DATA_UNAVAILABLE` rather than inventing values.

No live execution, risk, lot sizing, capital gating, SL or TP policy was modified.

## Phase U Pack 3.3.6 Handoff — Profile Execution / Research Separation

Verified intended operational state:

- P1 execution enabled, research enabled
- P2 execution disabled, research enabled
- P3 execution disabled, research enabled
- P4 execution enabled, research enabled

`enabled` remains true for P2/P3, preserving configuration and research participation. Re-enabling later requires only changing `execution_enabled` to true; no data migration is required.

Safety boundary: this pack does not certify real-account readiness and does not verify or change lot sizing, capital gating, maximum units, SL, TP, or execution protection parameters.

## Phase U Pack 3.3.7 Handoff — Phase U Pack 3.3 Closed

Phase U Pack 3.3 is complete after successful local execution of RUN_PHASE_U_PACK_3_3_7.ps1.

Operational state required by this phase:

- P1 execution enabled.
- P2 execution disabled; configuration/data/research preserved.
- P3 execution disabled; configuration/data/research preserved.
- P4 execution enabled.
- Live execution policy unchanged.

Next work must not claim real-account readiness until actual code and tests certify lot sizing, capital gating, maximum units, SL, TP, execution locks and P1/P4 profile configuration.

## Phase U Pack 3.3.10 Handoff

Status: COMPLETE

Production contracts are aligned:
- P1-P3 execution enabled
- P4 research-only execution disabled
- Universal historical timeframe contract includes M30

Validation evidence:
- pytest: 2409 passed
- AFIP Local Quality Check: PASS
- Dashboard generation: PASS

No trading logic change. Continue only after applying the documentation append and committing the validated patch.


## Phase U Pack 3.3.11 Handoff

Purpose: isolate reproducible runtime research data from Git before large historical research runs.

Apply order:
1. Extract pack over repository.
2. Run APPLY_PHASE_U_PACK_3_3_11.ps1.
3. Run RUN_PHASE_U_PACK_3_3_11.ps1.
4. Review git status and confirm runtime files still exist locally.
5. Commit and push only after validation passes.

Next planned pack: Phase U Pack 3.4.1 — Historical Dataset Readiness Certification, including completeness, duplicate, gap, invalid-bar, lineage, quarantine, and drawdown-research readiness requirements.

Safety: Pack 3.3.11 does not certify or arm P1 for real-money execution.


## Phase U Pack 3.4.1 Handoff

Historical Dataset Readiness Certification added.

Next target: Phase U Pack 3.4.2 Comprehensive Walk-Forward Research Engine.

Before Pack 3.4.2 research runs, certify the VPS historical dataset and retain the generated readiness report. Only READY and explicitly controlled CAUTION data may enter research. QUARANTINED data must remain isolated.

