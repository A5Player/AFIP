
## Latest Increment — Milestone J Pack 3
Conflict Resolver completed. Install after Milestone J Pack 2. Run targeted test, full pytest, local quality check, dashboard, then commit and push.

## Latest Increment — Milestone J Pack 4
Opportunity Ranking Engine added. Install after Milestone J Pack 3. Direct execution remains disabled. Next: Milestone J Pack 5 Trade Scoring Engine.

## Current Handoff — Milestone J Pack 5
Trade Scoring Engine completed. Continue with Milestone J Pack 6 Unit Allocation Engine. Live execution remains disabled.

## Milestone J Pack 6
Install after J Pack 5. Unit Allocation uses fixed 0.01-lot Units and passes only an explainable allocation context to Entry Validation. Direct execution remains disabled.

## Milestone J Pack 7
Install after J Pack 6. Entry Validation passes only an explainable approved context to paper/demo execution review. It never sends orders. Next: Milestone J Pack 8 Exit Validation Engine.

## Milestone J Pack 8
Install after J Pack 7. Exit Validation produces explainable paper/demo management context for HOLD, partial close, stop-loss move, take-profit change, trailing stop, or full exit. It never modifies or closes a live position. Next: Milestone J Pack 9 Portfolio Decision Engine.

## Latest Increment — Milestone J Pack 9
Portfolio Decision Engine added. Install after Milestone J Pack 8. Run targeted test, full pytest, local quality check, dashboard, then commit and push. Live execution remains disabled.

## Latest Increment — Milestone J Pack 10
Decision Intelligence Certification completed. Install after Milestone J Pack 9. Run targeted test, full pytest, local quality check, dashboard, then commit and push. Milestone J is complete when validation passes. Continue with Milestone K Pack 1 while live execution remains disabled.

## Latest — Milestone K Pack 1
Execution Intelligence Foundation added after Milestone J certification. Continue with Milestone K Pack 2 Smart Entry Engine. Preserve XM-only, GOLD#-only, 1 Unit = 0.01 lot, and LOCKED_SIMULATION_ONLY policy.

## Latest Increment — Milestone K Pack 2
Smart Entry Engine added with deterministic entry-price, stop-loss, take-profit, reward/risk, order-type, and fixed-unit validation. Dashboard explainability is available in English and Thai. No live order is sent. Continue from Milestone K Pack 3 — Smart Exit Engine.

## Latest Completed
Milestone K Pack 3 — Smart Exit Engine

Validation:
- Targeted: 6 passed
- Full pytest: 1150 passed
- AFIP Local Quality Check: PASS
- Dashboard generation: PASS
- Live execution remains disabled

Next:
Milestone K Pack 4 — Dynamic Stop Loss Intelligence

## Latest Increment: Milestone K Pack 4
Dynamic Stop Loss Intelligence added as an incremental patch. Install after Milestone K Pack 3. Validate with the included RUN script. Live execution remains disabled and no real position is modified.

## Latest: Milestone K Pack 5
Dynamic Take Profit Intelligence completed. Continue from Milestone K Pack 6 — Trailing Stop Intelligence after local validation and Git push.

## Latest: Milestone K Pack 6
Trailing Stop Intelligence completed. Install this patch after Milestone K Pack 5. Validate with `pytest tests/test_milestone_k_pack_6.py -v`, full pytest, local quality check, and dashboard generation. No real order or live position modification is permitted. Continue next with Milestone K Pack 7 — Partial Close Intelligence.

## Latest: Milestone K Pack 7
Partial Close Intelligence completed. Install this patch after Milestone K Pack 6. Validate with `pytest tests/test_milestone_k_pack_7.py -v`, full pytest, local quality check, and dashboard generation. Partial close is fixed-unit simulation only, preserves the configured runner, and never closes a live position. Continue next with Milestone K Pack 8 — Execution Supervisor.

## Latest: Milestone K Pack 8
Execution Supervisor completed. Install after Milestone K Pack 7. Validate with `pytest tests/test_milestone_k_pack_8.py -v`, full pytest, local quality check, and dashboard generation. The supervisor resolves competing execution-intelligence proposals into one simulation-only instruction and never sends an order. Continue next with Milestone K Pack 9 — Runtime Execution Certification.

## Latest: Milestone K Pack 9
Runtime Execution Certification completed. Install after Milestone K Pack 8. Validate with `pytest tests/test_milestone_k_pack_9.py -v`, full pytest, local quality check, and dashboard generation. Certification is deterministic and simulation-only; it never sends an order. Continue next with Milestone K Pack 10 — Execution Intelligence Complete.

## Latest: Milestone K Pack 10
Execution Intelligence Complete added. Install after Milestone K Pack 9. Validate with `pytest tests/test_milestone_k_pack_10.py -v`, full pytest, local quality check, and dashboard generation. When all gates pass, Milestone K is complete. Live and direct execution remain disabled and NO_ORDER_SENT remains mandatory. Continue next with Milestone L Pack 1.

## Latest: Milestone L Pack 1
Paper Execution Foundation completed. Install after Milestone K Pack 10. Validate with `pytest tests/test_milestone_l_pack_1.py -v`, full pytest, local quality check, and dashboard generation. This pack opens controlled paper/demo observation readiness only; it never transmits an order. Continue next with Milestone L Pack 2 while XM-only, GOLD#-only, fixed 0.01-lot Unit, LOCKED_SIMULATION_ONLY, and NO_ORDER_SENT policies remain mandatory.

## Latest: Milestone L Pack 2
Paper Execution Session Monitor completed. Install after Milestone L Pack 1. Validate with `pytest tests/test_milestone_l_pack_2.py -v`, full pytest, local quality check, and dashboard generation. The session monitor certifies data freshness, spread, latency, clock synchronization, risk, audit, and the permanent No-DCA policy. It records observations only and never transmits an order. Continue next with Milestone L Pack 3 while XM-only, GOLD#-only, fixed 0.01-lot Unit, LOCKED_SIMULATION_ONLY, and NO_ORDER_SENT remain mandatory.

## Latest: Milestone L Pack 3
Paper Decision Ledger completed. Install after Milestone L Pack 2. Validate with `pytest tests/test_milestone_l_pack_3.py -v`, full pytest, local quality check, and dashboard generation. Every paper action is recorded with deterministic identity, evidence, rejected alternatives, version context, and outcome-tracking readiness. Protected runners remain included in total exposure even when excluded from a new-entry ticket count. Traditional DCA and averaging down remain prohibited. Continue next with Milestone L Pack 4 while all live-execution locks remain mandatory.

## Latest: Milestone L Pack 4
Paper Outcome Evaluation completed. Install after Milestone L Pack 3. Validate with `pytest tests/test_milestone_l_pack_4.py -v`, full pytest, local quality check, and dashboard generation. The evaluator links deterministic paper decisions to chronological outcomes with MFE, MAE, costs, net profit, realized R, exit quality, and failure reason while blocking future leakage. Blocked outcomes never enter performance statistics or production knowledge. Traditional DCA and averaging down remain prohibited. Continue next with Milestone L Pack 5 while all live-execution locks remain mandatory.

## Latest: Milestone L Pack 5
Paper Performance Analytics completed. Install after Milestone L Pack 4. Validate with `pytest tests/test_milestone_l_pack_5.py -v`, full pytest, local quality check, and dashboard generation. The analytics runtime accepts only complete, chronological, future-safe Pack 4 outcomes and calculates auditable performance, risk, cost, and sample-quality statistics. Small samples remain explicitly uncertified. Traditional DCA and averaging down remain prohibited. Continue next with Milestone L Pack 6 while all live-execution locks remain mandatory.

## Latest: Milestone L Pack 6
Paper Performance Certification completed. Install after Milestone L Pack 5. Validate with `pytest tests/test_milestone_l_pack_6.py -v`, full pytest, local quality check, and dashboard generation. The certification runtime checks sample sufficiency, expectancy, profit factor, drawdown, cost ratio, positive net profit, data integrity, position policy, and execution safety. Passing certification permits controlled shadow observation only; demo and live execution remain disabled. Continue next with Milestone L Pack 7 while XM-only, GOLD#-only, fixed 0.01-lot Unit, No-DCA, LOCKED_SIMULATION_ONLY, and NO_ORDER_SENT remain mandatory.

## Latest: Milestone L Pack 7
Shadow Execution Observation completed. Install after Milestone L Pack 6. Validate with `pytest tests/test_milestone_l_pack_7.py -v`, full pytest, local quality check, and dashboard generation. Pack 7 observes certified decisions against live market-quality conditions without creating a broker request or transmitting an order. Traditional DCA and averaging down remain prohibited. Continue next with Milestone L Pack 8 while XM-only, GOLD#-only, fixed 0.01-lot Unit, LOCKED_SIMULATION_ONLY, and NO_ORDER_SENT remain mandatory.

## Latest: Milestone L Pack 8
Demo Execution Certification completed. Install after Milestone L Pack 7. Validate with `pytest tests/test_milestone_l_pack_8.py -v`, full pytest, local quality check, and dashboard generation. A READY result certifies controlled demo observation only; it does not permit broker requests or order transmission. Continue next with Milestone L Pack 9 — Production Release Candidate while XM-only, GOLD#-only, fixed 0.01-lot Unit, No-DCA, LOCKED_SIMULATION_ONLY, and NO_ORDER_SENT remain mandatory.

## Latest: Milestone L Pack 9
Production Release Candidate completed. Install after Milestone L Pack 8. Validate with `pytest tests/test_milestone_l_pack_9.py -v`, full pytest, local quality check, and dashboard generation. A READY result approves the Version 1.0 release candidate only; it does not enable demo or live execution and does not complete Production Certification. Continue next with Milestone L Pack 10 — Production Readiness Complete while XM-only, GOLD#-only, fixed 0.01-lot Unit, No-DCA, LOCKED_SIMULATION_ONLY, and NO_ORDER_SENT remain mandatory.


## Current Handoff — Milestone N Pack 3
- Portfolio Risk Engine implemented.
- Next: Milestone N Pack 4 — Capital Allocation.
- Apply patch only; do not regenerate repository.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Current Handoff — Milestone N Pack 4
- Capital Allocation implemented.
- Allocates only remaining risk, Unit, and margin capacity among independent trade plans.
- Preserves free-margin reserve, Portfolio Risk Engine lineage, protected-runner exposure, and No-DCA policy.
- Next: Milestone N Pack 5 under the locked Version 1.0 roadmap.
- Apply patch only; do not regenerate repository.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Current Handoff — Milestone N Pack 5
- Portfolio Exposure Coordination implemented.
- Install after Milestone N Pack 4 Capital Allocation.
- Validate with `pytest tests/test_milestone_n_pack_5.py -v`, full pytest, local quality check and dashboard generation.
- No broker request or order transmission is permitted.
- Next: Milestone N Pack 6 under the locked Version 1.0 roadmap.

## Regression Patch 1 — Dashboard Panel Registration
Status: COMPLETE

This patch fixes six existing dashboard registration regressions from Milestone L Pack 10 and Milestone M Packs 1–5. It modifies only dashboard composition and adds a regression test. No intelligence, trading, risk, allocation, or execution logic was changed.

Validation after applying Milestone N Packs 4–5 plus this patch:
- `pytest tests/test_regression_patch_1_dashboard_panel_registration.py -v`
- `pytest`
- `python tools/afip_local_quality_check.py`
- `python -m afip.dashboard_ui`

Execution remains permanently locked for Version 1.0 development.

## Current Handoff — Milestone N Pack 6
- Portfolio Drawdown Protection implemented.
- Validates equity floor, maximum drawdown, daily loss and consecutive loss limits after Pack 5 exposure coordination.
- Blocks new allocation when a protection gate fails; does not modify existing positions or send orders.
- Preserve valid Protected Runner positions and independent position lifecycles.
- Next: Milestone N Pack 7 under the locked Version 1.0 roadmap.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Milestone N Pack 7 — Portfolio Stress Validation
Completed deterministic research-only stress validation for portfolio allocation lineage. The runtime evaluates hypothetical spread, volatility, adverse-movement and liquidity conditions without creating, modifying, closing or transmitting orders. Continue from Milestone N Pack 8 after validation.

## Milestone N Pack 8 — Portfolio Resilience Certification
Completed deterministic research-only certification of Capital Allocation, Exposure Coordination, Drawdown Protection, and Stress Validation lineage. Continue from Milestone N Pack 9 after validation. Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Current Handoff — Milestone N Pack 9
- Portfolio Governance Validation implemented after Pack 8 Portfolio Resilience Certification.
- Validate with `pytest tests/test_milestone_n_pack_9.py -v`, full pytest, local quality check, and dashboard generation.
- Next: Milestone N Pack 10 — Portfolio Intelligence Complete.
- Apply patch only; do not regenerate repository.
- Execution remains LOCKED_SIMULATION_ONLY, Direct Execution false, Live Execution disabled, and NO_ORDER_SENT.

## Current Handoff — Milestone N Pack 10
- Milestone N Portfolio Intelligence is COMPLETE.
- Pack 10 validates Packs 1–9 capability completion, unique lineage, Portfolio Governance approval, data integrity, future safety, deterministic runtime, and permanent policy controls.
- A READY result permits progression only to Milestone O Pack 1 — Learning Intelligence Foundation.
- Production certification remains pending Milestone R.
- Apply patch only; do not regenerate repository or replace unrelated modules.
- Execution remains LOCKED_SIMULATION_ONLY, Direct Execution false, Live Execution disabled, and NO_ORDER_SENT.

## Current Handoff — Milestone O Pack 1
- Learning Intelligence Foundation implemented after Milestone N completion.
- Accepts only certified, chronological, future-safe observations as immutable research learning records.
- TRAINING, EVALUATION, and HOLDOUT roles remain separated.
- Automatic parameter updates, trading logic changes, and production knowledge promotion remain disabled.
- Validate with `pytest tests/test_milestone_o_pack_1.py -v`, full pytest, local quality check, and dashboard generation.
- Next: Milestone O Pack 2 — Learning Evidence Normalization.
- Execution remains LOCKED_SIMULATION_ONLY, Direct Execution false, Live Execution disabled, and NO_ORDER_SENT.

## Current Handoff — Milestone O Pack 2
- Learning Evidence Normalization implemented after Milestone O Pack 1.
- Converts accepted immutable Learning Records into deterministic canonical Evidence Records.
- TRAINING, EVALUATION, and HOLDOUT roles remain isolated.
- Non-finite values, invalid ranges, chronology violations, future leakage, uncertified lineage, adaptive updates, and execution authority are blocked.
- Validate with `pytest tests/test_milestone_o_pack_2.py -v`, full pytest, local quality check, and dashboard generation.
- Next: Milestone O Pack 3 — Learning Evidence Aggregation.
- Execution remains LOCKED_SIMULATION_ONLY, Direct Execution false, Live Execution disabled, and NO_ORDER_SENT.

## Current Handoff — Milestone O Pack 3
- Learning Evidence Aggregation implemented after Milestone O Pack 2.
- Aggregates only accepted, future-safe, chronological Pack 2 evidence with isolated dataset roles.
- Duplicate IDs, dataset contamination, invalid chronology, uncertified data, non-finite metrics, adaptive updates, and execution authority are blocked.
- Validate with `pytest tests/test_milestone_o_pack_3.py -v`, full pytest, local quality check, and dashboard generation.
- Next: Milestone O Pack 4 — Learning Performance Evaluation.
- Execution remains LOCKED_SIMULATION_ONLY, Direct Execution false, Live Execution disabled, and NO_ORDER_SENT.

## Latest Completed Work

Milestone O Pack 4 — Learning Performance Evaluation ✅

- Evaluates accepted Pack 3 aggregates across TRAINING and EVALUATION/HOLDOUT datasets.
- Produces deterministic weighted win/loss/breakeven rates, weighted realized R, total R, payoff ratio, and generalization gap.
- Blocks invalid lineage, duplicate aggregate IDs, missing evaluation datasets, chronology errors, future leakage, insufficient samples, non-finite values, data-quality failures, and locked-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Next: Milestone O Pack 5 — Learning Stability Validation.

## Latest Completed Work

Milestone O Pack 5 — Learning Stability Validation ✅

- Validates accepted Pack 4 performance evaluations across chronological research windows.
- Measures evaluation realized-R variability, generalization-gap stability, positive-window rate, stable-window rate, and sample coverage.
- Blocks duplicate IDs, chronology errors, future leakage, uncertified data, insufficient windows or samples, excessive variability, excessive generalization gap, poor positive-window coverage, and locked-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Next: Milestone O Pack 6 — Learning Drift Detection.

## Latest Completed Work

Milestone O Pack 6 — Learning Drift Detection ✅

- Compares accepted Pack 5 stability windows across certified baseline and recent research segments.
- Detects drift in mean evaluation realized R, mean generalization gap, and positive evaluation-window rate.
- Blocks duplicate IDs, chronology errors, future leakage, uncertified data, insufficient segment coverage, non-finite metrics, excessive drift, and locked-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Next: Milestone O Pack 7 — Learning Confidence Calibration.

## Latest Completed Work

Milestone O Pack 7 — Learning Confidence Calibration ✅

- Calibrates research confidence from accepted Pack 6 drift reports.
- Combines raw confidence, evidence coverage, realized-R drift stability, generalization stability, and positive-window consistency.
- Blocks duplicate IDs, chronology errors, future leakage, uncertified data, insufficient reports or samples, non-finite metrics, low calibrated confidence, and locked-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Next: Milestone O Pack 8 — Learning Validation Governance.

## Latest Completed Work

Milestone O Pack 9 — Learning Review Certification ✅

- Certifies documented manual review of accepted Pack 8 governance reports.
- Validates unique governance lineage, chronology, human reviewer identity, review-record integrity, approved research-continuation outcome, sample coverage, calibrated confidence, data quality, future safety, and frozen-policy compliance.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Next: Milestone O Pack 10 — Learning Intelligence Complete.

## Latest Completed Work

Milestone O Pack 10 — Learning Intelligence Complete ✅

- Milestone O Learning Intelligence is COMPLETE.
- Pack 10 validates Packs 1–9 capability completion, unique lineage, Pack 9 manual review certification, chronology, data integrity, future safety, deterministic runtime, dataset-role separation, and frozen policy controls.
- A READY result permits progression only to Milestone P Pack 1 — Market Behaviour Intelligence Foundation.
- Automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, and order transmission remain disabled.
- Production Certification remains pending Milestone R.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Validation commands:
- `pytest tests/test_milestone_o_pack_10.py -v`
- `pytest`
- `python tools/afip_local_quality_check.py`
- `python -m afip.dashboard_ui`

Next: Milestone P Pack 1 — Market Behaviour Intelligence Foundation.

## Latest Completed Work

Milestone P Pack 4 — Market Behaviour Transition Statistics ✅

Validation target: `tests/test_milestone_p_pack_4.py`

Next: Milestone P Pack 5 — Market Behaviour Stability Validation

Execution remains `LOCKED_SIMULATION_ONLY`; direct and live execution remain disabled; no order is sent.

## Latest Completed Work

Milestone P Pack 5 — Market Behaviour Stability Validation ✅

- Validates accepted Pack 4 transition statistics across chronological research windows.
- Measures persistence variability, change-rate variability, dominant regime/behaviour consistency, stable-window rate, and transition coverage.
- Blocks duplicate IDs, chronology errors, future leakage, uncertified data, insufficient coverage, invalid metrics, excessive variability, poor consistency, and locked-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Next: Milestone P Pack 6 — Market Behaviour Drift Detection.

## Latest Completed Work

Milestone P Pack 6 — Market Behaviour Drift Detection ✅

- Compares accepted Pack 5 stability reports across chronological baseline and recent research segments.
- Measures drift in mean persistence, regime-change rate, behaviour-change rate, and stable-window rate.
- Blocks invalid Pack 5 lineage, duplicate report IDs, insufficient windows or transition coverage, chronology errors, future leakage, uncertified data, invalid metrics, drift-limit breaches, and locked-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Validation commands:
- `pytest tests/test_milestone_p_pack_6.py -v`
- `pytest`
- `python tools/afip_local_quality_check.py`
- `python -m afip.dashboard_ui`

Next: Milestone P Pack 7 — Market Behaviour Confidence Calibration.

## Latest Completed Work

Milestone P Pack 7 — Market Behaviour Confidence Calibration ✅

- Calibrates research confidence from accepted Pack 6 behaviour-drift reports.
- Measures evidence coverage, persistence stability, regime/behaviour change-rate stability, and stable-window consistency.
- Blocks invalid lineage, duplicate IDs, chronology errors, future leakage, uncertified data, insufficient coverage, non-finite metrics, low confidence, and frozen-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Validation commands:
- `pytest tests/test_milestone_p_pack_7.py -v`
- `pytest`
- `python tools/afip_local_quality_check.py`
- `python -m afip.dashboard_ui`

Next: Milestone P Pack 8 — Market Behaviour Validation Governance.

## Latest Completed Work

Milestone P Pack 9 — Market Behaviour Review Certification ✅

- Certifies documented manual review for accepted Pack 8 market-behaviour governance reports.
- Validates PBGV lineage, review chronology, manual reviewer identity, PBREV record, approved research-continuation outcome, transition coverage, confidence, data quality, future safety, Market Regime ordering, and frozen policy controls.
- Research only. Automatic parameter update, trading-logic change, production knowledge promotion, Production Certification, position modification, broker request, and order transmission remain disabled.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Validation commands:
- `pytest tests/test_milestone_p_pack_9.py -v`
- `pytest`
- `python tools/afip_local_quality_check.py`
- `python -m afip.dashboard_ui`

Next: Milestone P Pack 10 — Market Behaviour Intelligence Complete.

## Latest Completed Work

Milestone P Pack 10 — Market Behaviour Intelligence Complete ✅

- Certifies Packs 1–9 as complete with unique capability lineage and accepted Pack 9 manual review certification.
- Validates chronology, data quality, future safety, deterministic runtime, Market Regime before Behaviour, and Version 1.0 frozen policy.
- Milestone P is complete for research-only progression.
- Production Certification remains pending Milestone R.
- Automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, and order transmission remain disabled.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Validation commands:
- `pytest tests/test_milestone_p_pack_10.py -v`
- `pytest`
- `python tools/afip_local_quality_check.py`
- `python -m afip.dashboard_ui`

Next: Milestone Q Pack 1 — Market Intent Intelligence Foundation.

## Latest Completed Work

Milestone Q Pack 1 — Market Intent Intelligence Foundation ✅

- Introduces immutable deterministic research-only Market Intent observations.
- Requires certified Market Regime and Market Behaviour evidence to be evaluated before Intent.
- Classifies BUYING_PRESSURE, SELLING_PRESSURE, LIQUIDITY_SEEKING, BREAKOUT_ATTEMPT, REVERSAL_ATTEMPT, and BALANCED_INTENT.
- Blocks invalid chronology, future leakage, uncertified data, invalid lineage values, invalid metrics, and frozen-policy violations.
- No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Validation commands:
- `pytest tests/test_milestone_q_pack_1.py -v`
- `pytest`
- `python tools/afip_local_quality_check.py`
- `python -m afip.dashboard_ui`

Next: Milestone Q Pack 2 — Market Intent State Normalization.
