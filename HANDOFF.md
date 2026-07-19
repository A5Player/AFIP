
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

