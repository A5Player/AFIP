
## Milestone J Pack 3 — Conflict Resolver
- Deterministic evidence-conflict classification and resolution.
- High unresolved conflict forces WAIT.
- Bilingual dashboard explainability.
- Direct execution remains disabled.

## Milestone J Pack 5 — Trade Scoring Engine
- Deterministic scoring after opportunity ranking.
- Direct execution remains disabled.

## Milestone J Pack 6 — Unit Allocation Engine
- 1 Unit = 0.01 lot; lot per Unit never increases.
- Allocation constrained by profile, capital, risk, and trade grade.
- Direct execution and live execution remain disabled.

## Milestone J Pack 7 — Entry Validation Engine
- Deterministic pre-entry validation after fixed Unit allocation.
- Checks Market Regime, unresolved conflict, trade score, risk, timing, spread/trading cost, and allocation policy.
- 1 Unit remains fixed at 0.01 lot.
- Direct execution and live execution remain disabled.

## Milestone J Pack 8 — Exit Validation Engine
- Deterministic validation for HOLD, PARTIAL_CLOSE, MOVE_STOP_LOSS, CHANGE_TAKE_PROFIT, TRAIL_STOP, and EXIT.
- Dashboard explains Holding, Stop Loss Move, Take Profit Change, Trailing Stop, Partial Close, and Exit reasons in English and Thai.
- XM only and GOLD# only.
- Direct execution and live execution remain disabled.

## Milestone J Pack 9 — Portfolio Decision Engine
- Added deterministic portfolio-level decision context.
- Combines entry, exit, risk, exposure, and fixed-unit capacity.
- Decisions remain non-executing and explainable in English and Thai.
- Version 1 remains XM-only, GOLD#-only, and LOCKED_SIMULATION_ONLY.

## Milestone J Pack 10 — Decision Intelligence Certification
- Milestone J certification layer completed.
- Certifies Market Regime V2, Decision Foundation, Consensus, Conflict Resolution, Opportunity Ranking, Trade Scoring, Unit Allocation, Entry Validation, Exit Validation, and Portfolio Decision.
- Version 1 remains XM-only and GOLD#-only.
- 1 Unit remains fixed at 0.01 lot.
- Direct execution and live execution remain disabled.
- Next milestone: Milestone K — Execution Intelligence.

## Milestone K Pack 1 — Execution Intelligence Foundation
- Added deterministic simulation-readiness execution gate.
- Added policy, risk, timing, cost, market, calendar, fixed-unit, and certification checks.
- Added bilingual dashboard explainability.
- No order is sent; live and direct execution remain disabled.

## Milestone K Pack 2 — Smart Entry Engine
- Status: COMPLETED
- Scope: XM / GOLD# / simulation-only protected entry planning
- Unit policy: 1 Unit = 0.01 Lot
- Direct execution: disabled
- Live execution: disabled

## Milestone K Pack 3 — Smart Exit Engine
- Status: COMPLETE
- Targeted tests: 6 passed
- Full pytest: 1150 passed
- Local Quality Check: PASS
- Dashboard: PASS
- Actions: HOLD, PARTIAL_CLOSE, EXIT
- Execution: LOCKED_SIMULATION_ONLY
- Live execution: DISABLED
- Direct execution: False
- Unit policy: 1 Unit = 0.01 Lot

## Milestone K Pack 4 — Dynamic Stop Loss Intelligence
- Added deterministic stop-loss review for paper/demo simulation.
- Stop moves must reduce risk and respect BUY/SELL geometry.
- Added EN/TH dashboard explainability.
- XM Only, GOLD# Only, 1 Unit = 0.01 Lot.
- Live and direct execution remain disabled.

## Milestone K Pack 5 — Dynamic Take Profit Intelligence
- Status: completed
- Scope: simulation-only take-profit review and bilingual dashboard explainability
- Policy: XM only, GOLD# only, 1 Unit = 0.01 Lot, live/direct execution disabled

## Milestone K Pack 6 — Trailing Stop Intelligence
- Status: completed as an incremental production-quality patch.
- Added deterministic trailing-stop readiness, break-even detection, profit locking, and multi-stage trailing.
- Validates BUY/SELL geometry, current and proposed stop loss, minimum locked profit, trading cost, risk, timing, and market structure.
- Added holding reason, trailing-stop reason, expected next action, confidence, next review time, and EN/TH dashboard explainability.
- XM only, GOLD# only, 1 Unit = 0.01 Lot.
- Execution remains LOCKED_SIMULATION_ONLY; Direct Execution is False; Live Execution is disabled; NO_ORDER_SENT.

## Milestone K Pack 7 — Partial Close Intelligence
- Status: completed as an incremental production-quality patch.
- Added deterministic fixed-unit partial-close readiness for paper/demo simulation.
- Validates BUY/SELL profit direction, requested and remaining Units, minimum runner, profit, trading cost, risk, timing, and market structure.
- 1 Unit remains fixed at 0.01 lot; partial close cannot increase lot size or close all Units.
- Added holding reason, partial-close reason, expected next action, confidence, next review time, and EN/TH dashboard explainability.
- XM only, GOLD# only, LOCKED_SIMULATION_ONLY, Direct Execution False, Live Execution disabled, NO_ORDER_SENT.

## Milestone K Pack 8 — Execution Supervisor
- Status: completed as an incremental production-quality patch.
- Added deterministic central supervision across entry and open-position management proposals.
- Resolves conflicting actions using financial-risk priority: emergency/full exit, partial close, trailing stop, stop-loss move, take-profit change, entry, then hold.
- Validates position state, fixed Unit policy, risk, timing, trading cost, Market Structure, Market Regime, and dependency reports.
- Produces one simulation-only approved action with rejected-action visibility and EN/TH explanations.
- XM only, GOLD# only, 1 Unit = 0.01 lot, LOCKED_SIMULATION_ONLY, Direct Execution False, Live Execution disabled, NO_ORDER_SENT.

## Milestone K Pack 9 — Runtime Execution Certification
- Status: completed as an incremental production-quality patch.
- Added deterministic certification after Execution Supervisor.
- Certifies all Execution Intelligence dependencies, approved-action consistency, Position State, fixed Unit policy, XM/GOLD# policy, simulation lock, live/direct execution guards, and NO_ORDER_SENT.
- Added deterministic certification ID, audit readiness, block reasons, confidence, next review time, and EN/TH dashboard explainability.
- XM only, GOLD# only, 1 Unit = 0.01 lot, LOCKED_SIMULATION_ONLY, Direct Execution False, Live Execution disabled, NO_ORDER_SENT.

## Milestone K Pack 10 — Execution Intelligence Complete
- Added deterministic Milestone K completion gate for Packs 1-9.
- Added runtime certification, dashboard explainability, audit-chain, policy, and execution-safety completion checks.
- Added deterministic completion ID and bilingual Dashboard explainability.
- Milestone K is complete only when all checks pass.
- XM Only; GOLD# Only; 1 Unit = 0.01 Lot.
- LOCKED_SIMULATION_ONLY; Direct Execution=False; Live Execution Disabled; NO_ORDER_SENT.
- Next: Milestone L Pack 1.

## Milestone L Pack 1 — Paper Execution Foundation
- Status: completed as an incremental production-quality patch.
- Opens Milestone L only after Milestone K completion and runtime certification.
- Validates paper-account connectivity, market data, historical data, risk limits, audit, and dashboard explainability readiness.
- Adds deterministic Paper Execution Foundation ID and EN/TH dashboard explanations.
- XM only, GOLD# only, and 1 Unit = 0.01 lot remain mandatory.
- Execution remains LOCKED_SIMULATION_ONLY; Direct Execution is False; Live Execution is disabled; NO_ORDER_SENT remains mandatory.

## Milestone L Pack 2 — Paper Execution Session Monitor
- Status: completed as an incremental production-quality patch.
- Adds deterministic paper-session readiness after Milestone L Pack 1.
- Certifies paper account connectivity, market-session availability, data freshness, spread, latency, clock synchronization, risk limits, and audit readiness.
- Requires Independent Trade Plans and permanently disables Traditional DCA and averaging down.
- Old profitable protected runners may be managed independently in future packs, but all positions remain included in total exposure and risk.
- Adds bilingual dashboard explainability, deterministic Observation ID, block reasons, confidence, and next review time.
- XM only, GOLD# only, 1 Unit = 0.01 Lot.
- LOCKED_SIMULATION_ONLY, Direct Execution False, Live Execution disabled, NO_ORDER_SENT.
- Next: Milestone L Pack 3.

## Milestone L Pack 3 — Paper Decision Ledger
- Status: COMPLETE
- Adds deterministic decision IDs and paper-decision audit records.
- Records approved action, position state, direction, units, independent trade plan, market context, news context, confidence evidence, rejected alternatives, version context, and outcome-tracking readiness.
- Protected runners may be excluded from the new-entry ticket count only when protected; all positions remain included in total exposure and risk.
- Traditional DCA and averaging down remain disabled.
- Execution remains LOCKED_SIMULATION_ONLY with Direct Execution disabled, Live Execution disabled, and NO_ORDER_SENT.

## Milestone L Pack 4 — Paper Outcome Evaluation
- Status: COMPLETE
- Links each accepted Pack 3 paper decision to a deterministic outcome identity.
- Records chronological market outcome, MFE, MAE, gross profit, trading cost, swap cost, net profit, planned risk, realized R, exit quality, and failure reason.
- Blocks future leakage, invalid chronology, incomplete data, missing decision linkage, missing closed-outcome risk, and excluded protected-runner exposure.
- Blocked outcomes do not enter performance statistics or production knowledge.
- Independent position lifecycles remain mandatory; traditional DCA and averaging down remain disabled.
- Execution remains LOCKED_SIMULATION_ONLY with Direct Execution disabled, Live Execution disabled, and NO_ORDER_SENT.

## Milestone L Pack 5 — Paper Performance Analytics
- Status: COMPLETE
- Aggregates only accepted, chronological Pack 4 paper outcomes.
- Calculates sample counts, win rate, gross profit, gross loss, net profit, profit factor, average realized R, expectancy R, maximum drawdown, trading cost, swap cost, and cost ratio.
- Rejects future-information, incomplete, unlinked, non-closed, or blocked outcomes from performance statistics.
- Tracks minimum sample sufficiency without treating a small sample as production proof.
- Independent position lifecycles remain mandatory; protected runners remain included in total exposure and risk.
- Traditional DCA and averaging down remain disabled.
- Execution remains LOCKED_SIMULATION_ONLY with Direct Execution disabled, Live Execution disabled, and NO_ORDER_SENT.

## Milestone L Pack 6 — Paper Performance Certification
- Status: COMPLETE
- Certifies the Pack 5 paper-performance baseline against minimum sample, expectancy, profit factor, drawdown, cost ratio, positive net profit, and data-integrity gates.
- Produces a deterministic certification ID and bilingual explainability.
- Certification permits controlled shadow observation only; demo execution remains separately gated and disabled.
- Independent position lifecycles remain mandatory; protected runners remain included in total exposure and risk.
- Traditional DCA and averaging down remain disabled.
- XM only, GOLD# only, and 1 Unit = 0.01 Lot remain mandatory.
- Execution remains LOCKED_SIMULATION_ONLY with Direct Execution disabled, Live Execution disabled, and NO_ORDER_SENT.

## Milestone L Pack 7 — Shadow Execution Observation
- Status: COMPLETE
- Observes a Pack 6-certified decision against current market and execution conditions.
- Links Pack 6 certification and Pack 3 Decision IDs.
- Validates BUY/SELL geometry, data freshness, market session, spread, latency, risk, timing, and market structure.
- Creates a deterministic Shadow Observation ID with bilingual dashboard explainability.
- Requires Independent Trade Plans and includes Protected Runner positions in total exposure.
- Traditional DCA and averaging down remain disabled.
- Does not create a broker request and does not attempt order transmission.
- XM only, GOLD# only, and 1 Unit = 0.01 Lot remain mandatory.
- Execution remains LOCKED_SIMULATION_ONLY with Direct Execution disabled, Live Execution disabled, and NO_ORDER_SENT.

## Milestone L Pack 8 — Demo Execution Certification
- Status: COMPLETE
- Aggregates chronological Pack 7 Shadow Observation evidence.
- Preserves Pack 6 Performance Certification lineage.
- Validates minimum sample, readiness rate, spread pass rate, latency pass rate, market quality, risk, timing, and market structure.
- Requires unique Shadow Observation IDs and chronological integrity.
- Requires Independent Trade Plans and includes Protected Runner positions in total exposure.
- Traditional DCA and averaging down remain disabled.
- Creates a deterministic Demo Certification ID with bilingual dashboard explainability.
- READY certifies controlled demo observation only; demo order transmission remains disabled.
- XM only, GOLD# only, and 1 Unit = 0.01 Lot remain mandatory.
- Execution remains LOCKED_SIMULATION_ONLY with Direct Execution disabled, Live Execution disabled, and NO_ORDER_SENT.

## Milestone L Pack 9 — Production Release Candidate
- Status: COMPLETE
- Aggregates readiness from Milestone L Packs 1-8 into a deterministic Version 1.0 Production Release Candidate gate.
- Requires Demo Execution Certification lineage, all Pack dependencies, Production Health Monitor, Emergency Safety System, Production Report, Decision Ledger, Data Quality Certification, Knowledge Versioning, Feature Flags, bilingual Operation Manuals, and audit-chain readiness.
- Requires Independent Trade Plans and includes Protected Runner positions in total exposure and risk.
- Traditional DCA and averaging down remain disabled.
- Produces a deterministic Release Candidate ID and bilingual Dashboard explainability.
- A READY result approves a release candidate only; Production Certification remains False.
- XM only, GOLD# only, and 1 Unit = 0.01 Lot remain mandatory.
- Execution remains LOCKED_SIMULATION_ONLY with Direct Execution disabled, Live Execution disabled, and NO_ORDER_SENT.


## Milestone N Pack 3 — Portfolio Risk Engine
- Status: Implemented
- Research-only deterministic portfolio risk aggregation and approval gate.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.
- Version 1.0 roadmap now completes at Milestone R.

## Milestone N Pack 4 — Capital Allocation
- Status: IMPLEMENTED
- Adds deterministic, research-only allocation of remaining portfolio risk, fixed Units, and margin capacity among independent trade plans.
- Uses Portfolio Risk Engine approval and lineage from Pack 3.
- Preserves the configured minimum free-margin reserve and maximum portfolio Unit ceiling.
- Allocates in deterministic priority order and records full, partial, blocked, or no-capacity outcomes per trade plan.
- Requires unique Independent Trade Plans and independent position lifecycles.
- Protected Runner exposure remains included in portfolio exposure and risk.
- Traditional DCA, Averaging Down, Martingale, Grid Trading, and Recovery Trading remain disabled.
- XM only, GOLD# only, and 1 Unit = 0.01 Lot remain mandatory.
- Execution remains LOCKED_SIMULATION_ONLY with Direct Execution disabled, Live Execution disabled, and NO_ORDER_SENT.

## Milestone N Pack 5 — Portfolio Exposure Coordination

- Added deterministic research-only coordination of allocated BUY/SELL exposure.
- Validates portfolio unit, total-risk, direction-concentration and Protected Runner limits.
- Preserves independent Trade Plan and Position lifecycles.
- Preserves XM-only, GOLD#-only and fixed 0.01-lot Unit policy.
- Traditional DCA, Averaging Down, Martingale, Grid Trading and Recovery Trading remain prohibited.
- Execution remains `LOCKED_SIMULATION_ONLY`, Direct Execution remains false and no order is sent.

## Regression Patch 1 — Dashboard Panel Registration
- Scope: Regression fix only; no new trading capability.
- Registered existing Milestone L Pack 10 and Milestone M Packs 1–5 reports in `DashboardUIRuntime`.
- Restored panel IDs: `production_readiness_complete`, `knowledge_intelligence_foundation`, `pattern_knowledge_engine`, `pattern_similarity_search`, `pattern_clustering`, `pattern_statistics`.
- Trading logic unchanged. Execution remains `LOCKED_SIMULATION_ONLY`, direct execution false, live execution disabled, and order status `NO_ORDER_SENT`.
- Validation: 1375 tests passed including the dedicated regression test; local quality check PASS; dashboard generation PASS.

## Milestone N Pack 6 — Portfolio Drawdown Protection
- Status: IMPLEMENTED
- Adds deterministic research-only equity-floor, maximum-drawdown, daily-loss, and consecutive-loss protection after Portfolio Exposure Coordination.
- A blocked result requires reducing or stopping new allocation; it never modifies a position or creates a broker request.
- Existing valid Protected Runner positions remain preserved and included in portfolio exposure.
- Independent position lifecycles and all permanent Version 1.0 trading policies remain mandatory.
- Execution remains LOCKED_SIMULATION_ONLY, Direct Execution false, Live Execution disabled, and NO_ORDER_SENT.

## Milestone N Pack 7 — Portfolio Stress Validation
- Status: COMPLETE
- Scope: deterministic research-only portfolio stress validation
- Validates stressed equity floor, stressed drawdown, liquidity buffer and Pack 4–6 lineage
- Trading logic changed: No
- Execution authority: None
- Execution status: LOCKED_SIMULATION_ONLY

## Milestone N Pack 8 — Portfolio Resilience Certification
- Status: COMPLETE
- Consolidates approved lineage from Milestone N Packs 4–7 into one deterministic research-only certification gate.
- Requires Capital Allocation, Exposure Coordination, Drawdown Protection, and Stress Validation approvals and identifiers.
- Requires data quality, future-safe evidence, Market Regime before Signal, independent position lifecycles, and Protected Runner preservation.
- Traditional DCA, Averaging Down, Martingale, Grid Trading, and Recovery Trading remain disabled.
- XM only, GOLD# only, and 1 Unit = 0.01 Lot remain mandatory.
- No broker request, order transmission, position modification, or trading-logic change is permitted.
- Execution remains LOCKED_SIMULATION_ONLY, Direct Execution false, Live Execution disabled, and NO_ORDER_SENT.

## Milestone N Pack 9 — Portfolio Governance Validation
- Added deterministic portfolio governance validation after Pack 8 resilience certification.
- Validates frozen Version 1.0 policy, configuration integrity, audit lineage, authority separation, override prohibition, lifecycle independence, protected runner preservation, and permanent forbidden-method policy.
- Research-only; no broker request, order transmission, position modification, or trading-logic change.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Milestone N Pack 10 — Portfolio Intelligence Complete
- Status: COMPLETE
- Closes Milestone N Portfolio Intelligence under the Version 1.0 Feature Freeze.
- Verifies completion and unique lineage for Packs 1–9.
- Requires approved Portfolio Governance, data quality, future-safe evidence, deterministic runtime, and Market Regime before Signal.
- Requires independent trade plans, independent position lifecycles, and Protected Runner preservation.
- Traditional DCA, Averaging Down, Martingale, Grid Trading, and Recovery Trading remain disabled.
- XM only, GOLD# only, and 1 Unit = 0.01 Lot remain mandatory.
- Production certification is not granted; Milestone R remains required.
- Next: Milestone O Pack 1 — Learning Intelligence Foundation.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Milestone O Pack 1 — Learning Intelligence Foundation
Status: COMPLETE

- Adds deterministic immutable research learning records from certified chronological observations.
- Separates TRAINING, EVALUATION, and HOLDOUT dataset roles.
- Blocks future leakage, uncertified sources, invalid chronology, mutable records, automatic parameter updates, trading logic changes, and production knowledge promotion.
- Requires Milestone N Portfolio Intelligence completion lineage.
- Next: Milestone O Pack 2 — Learning Evidence Normalization.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Milestone O Pack 2 — Learning Evidence Normalization
Status: COMPLETE

- Normalizes accepted immutable Pack 1 learning records into canonical research evidence records.
- Standardizes dataset role, outcome, direction, Market Regime, confidence, realized R, MFE, MAE, cost ratio, duration, and sample weight.
- Requires Pack 1 acceptance, immutable lineage, certified data quality, valid chronology, and future-safe evidence.
- Blocks non-finite metrics, out-of-range metrics, invalid financial labels, dataset contamination, adaptive updates, trading logic changes, production knowledge promotion, and all execution authority.
- Next: Milestone O Pack 3 — Learning Evidence Aggregation.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Milestone O Pack 3 — Learning Evidence Aggregation
Status: COMPLETE

- Aggregates only accepted Pack 2 canonical evidence into deterministic research statistics.
- Preserves TRAINING, EVALUATION, and HOLDOUT isolation.
- Validates unique evidence IDs, chronology, data quality, future safety, finite metrics, financial labels, and locked policy.
- Produces weighted sample counts, outcome counts, average confidence, realized R, MFE, MAE, costs, and duration.
- Automatic parameter updates, trading logic changes, production knowledge promotion, broker requests, position modification, and order transmission remain forbidden.
- Next: Milestone O Pack 4 — Learning Performance Evaluation.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Milestone O Pack 4 — Learning Performance Evaluation

Status: COMPLETE

Added deterministic research-only performance evaluation for accepted Milestone O Pack 3 aggregates. The runtime validates dataset coverage, chronology, future safety, sample sufficiency, data quality, locked policy compliance, weighted performance statistics, and training-to-evaluation generalization gap. It cannot update parameters, change trading logic, promote production knowledge, modify positions, or transmit orders.

Validation: 8 targeted tests passed; 1447 full tests passed; AFIP Local Quality Check PASS; Dashboard generation PASS.

## Milestone O Pack 5 — Learning Stability Validation

Status: COMPLETE

Added deterministic research-only stability validation for accepted Milestone O Pack 4 performance evaluations across chronological research windows. The runtime validates window count, total sample coverage, dataset coverage, unique lineage, chronology, future safety, data quality, evaluation variability, generalization gap, and positive evaluation-window rate. It cannot update parameters, change trading logic, promote production knowledge, modify positions, or transmit orders.

Validation: 8 targeted tests passed; 1455 full tests passed; AFIP Local Quality Check PASS; Dashboard generation PASS.

## Milestone O Pack 6 — Learning Drift Detection

Status: COMPLETE

Added deterministic research-only drift detection for accepted Milestone O Pack 5 stability validation windows. The runtime compares certified baseline and recent segments for mean evaluation realized R, mean generalization gap, and positive evaluation-window rate. It validates unique Pack 5 lineage, chronology, future safety, data quality, sample coverage, finite metrics, and locked policy compliance. It cannot update parameters, change trading logic, promote production knowledge, modify positions, or transmit orders.

Validation: 8 targeted tests passed; 1463 full tests passed; AFIP Local Quality Check PASS; Dashboard generation PASS.

## Milestone O Pack 7 — Learning Confidence Calibration

Status: COMPLETE

Added deterministic research-only confidence calibration for accepted Milestone O Pack 6 drift reports. The runtime validates unique Pack 6 lineage, chronology, future safety, data quality, sample coverage, finite metrics, locked policy compliance, and minimum calibrated confidence. It combines raw research confidence, evidence coverage, realized-R drift stability, generalization stability, and positive-window consistency into a bounded confidence score and band. It cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

Validation: 8 targeted tests passed; 1471 full tests passed; AFIP Local Quality Check PASS; Dashboard generation PASS.

## Milestone O Pack 9 — Learning Review Certification ✅
- Added deterministic certification of documented manual review for accepted Pack 8 governance reports.
- Validates unique OGOV lineage, chronology, reviewer identity, review record, approved research-continuation outcome, coverage, confidence, data quality, future safety, and frozen-policy controls.
- Certification remains research-only and does not authorize parameter updates, trading-logic changes, production knowledge promotion, position modification, broker requests, or order transmission.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.
- Validation: targeted 8 passed; full pytest 1487 passed; local quality check PASS; dashboard generation PASS.
- Next: Milestone O Pack 10 — Learning Intelligence Complete.

## Milestone O Pack 10 — Learning Intelligence Complete

Status: COMPLETE

- Closes Milestone O Learning Intelligence under the AFIP Version 1.0 Feature Freeze.
- Validates complete and unique capability lineage for Packs 1–9.
- Requires accepted Pack 9 documented manual review certification.
- Requires certified data quality, future-safe evidence, deterministic runtime, dataset-role separation, and chronological completion.
- Confirms XM only, GOLD# only, and 1 Unit = 0.01 Lot.
- Does not grant automatic parameter updates, trading-logic changes, production knowledge promotion, broker requests, position modification, order transmission, or Production Certification.
- Production Certification remains pending Milestone R.
- Next: Milestone P Pack 1 — Market Behaviour Intelligence Foundation.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

Validation: 8 targeted tests passed; 1495 full tests passed; AFIP Local Quality Check PASS; Dashboard generation PASS.

## Milestone P Pack 4 — Market Behaviour Transition Statistics

Status: COMPLETE

Added deterministic, immutable, research-only aggregation of certified Milestone P Pack 3 sequence reports. The runtime calculates transition frequencies, persistence, regime/behaviour/direction change rates, dominant states, and lineage validation while preserving Feature Freeze and LOCKED_SIMULATION_ONLY execution policy.

## Milestone P Pack 5 — Market Behaviour Stability Validation ✅

- Added `afip/market_behaviour_stability_validation`.
- Validates certified Pack 4 transition-statistics reports across chronological research windows.
- Measures persistence variability, regime/behaviour change-rate variability, dominant-state consistency, stable-window rate, and sample coverage.
- Blocks invalid lineage, duplicates, insufficient windows or transitions, chronology errors, future leakage, uncertified data, invalid metrics, excessive variability, low consistency, and frozen-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Validation: 8 targeted tests passed; 1535 full tests passed; local quality and dashboard passed.

Next: Milestone P Pack 6 — Market Behaviour Drift Detection.

## Milestone P Pack 6 — Market Behaviour Drift Detection ✅

- Added `afip/market_behaviour_drift_detection`.
- Compares accepted Pack 5 stability reports across certified baseline and recent research segments.
- Detects drift in persistence, regime/behaviour change rates, and stable-window rate.
- Blocks invalid lineage, duplicate IDs, insufficient segment coverage, chronology errors, future leakage, uncertified data, invalid metrics, excessive drift, and frozen-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Validation: 8 targeted tests passed; 1543 full tests passed; local quality and dashboard passed.

Next: Milestone P Pack 7 — Market Behaviour Confidence Calibration.

## Milestone P Pack 7 — Market Behaviour Confidence Calibration ✅

- Added `afip/market_behaviour_confidence_calibration`.
- Calibrates deterministic research confidence from accepted Pack 6 behaviour-drift reports.
- Combines raw drift confidence, transition coverage, persistence stability, regime-change stability, behaviour-change stability, and stable-window consistency.
- Blocks invalid Pack 6 lineage, duplicate report IDs, chronology errors, future leakage, uncertified data, insufficient report or transition coverage, non-finite metrics, low calibrated confidence, and frozen-policy violations.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Validation: 8 targeted tests passed; 1551 full tests passed; local quality and dashboard passed.

Next: Milestone P Pack 8 — Market Behaviour Validation Governance.

## Milestone P Pack 9 — Market Behaviour Review Certification ✅

- Added `afip/market_behaviour_review_certification`.
- Certifies documented manual review of accepted Pack 8 market-behaviour governance reports.
- Validates unique PBGV lineage, chronology, reviewer identity, PBREV review record, approved research-continuation outcome, transition coverage, confidence, data quality, future safety, Market Regime order, and frozen-policy controls.
- Certification remains research-only and does not authorize parameter updates, trading-logic changes, production knowledge promotion, Production Certification, position modification, broker requests, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Validation: 8 targeted tests passed; 1567 full tests passed; local quality check PASS; dashboard generation PASS.

Next: Milestone P Pack 10 — Market Behaviour Intelligence Complete.

## Milestone P Pack 10 — Market Behaviour Intelligence Complete ✅

- Added `afip/market_behaviour_intelligence_complete`.
- Closes Milestone P under AFIP Version 1.0 Feature Freeze.
- Validates complete and unique capability lineage for Packs 1–9.
- Requires accepted Pack 9 documented manual review certification.
- Requires certified data quality, future safety, deterministic runtime, Market Regime before Behaviour, chronological completion, and frozen execution policy.
- Research only. Does not authorize automatic parameter updates, trading-logic changes, production knowledge promotion, Production Certification, position modification, broker requests, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Validation: 8 targeted tests passed; 1575 full tests passed; local quality check PASS; dashboard generation PASS.

Next: Milestone Q Pack 1 — Market Intent Intelligence Foundation.

## Milestone Q Pack 1 — Market Intent Intelligence Foundation ✅

- Added `afip/market_intent_intelligence_foundation`.
- Creates deterministic, immutable, research-only Market Intent observations.
- Requires certified data, valid chronology, future-safe inputs, Market Regime before Intent, and Market Behaviour before Intent.
- Supports BUYING_PRESSURE, SELLING_PRESSURE, LIQUIDITY_SEEKING, BREAKOUT_ATTEMPT, REVERSAL_ATTEMPT, and BALANCED_INTENT.
- Broker remains XM Only; symbol remains GOLD# Only; base unit remains 0.01 lot.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.
- No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission authority was introduced.

Next: Milestone Q Pack 2 — Market Intent State Normalization.

## Milestone Q Pack 2 — Market Intent State Normalization ✅

- Added `afip/market_intent_state_normalization`.
- Normalizes accepted Pack 1 Market Intent observations into the canonical immutable research schema.
- Produces dominant pressure, intent intensity, intensity band, continuation/reversal balance, and directional alignment.
- Requires valid QINT lineage, certified data, future-safe chronology, Market Regime before Intent, Market Behaviour before Intent, valid labels, valid metrics, and frozen-policy compliance.
- Broker remains XM Only; symbol remains GOLD# Only; base unit remains 0.01 lot.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, Production Certification, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Next: Milestone Q Pack 3 — Market Intent Sequence Analysis.

---

## Milestone Q Pack 3 — Market Intent Sequence Analysis

Status: Implemented

Added a deterministic and immutable research-only sequence analysis layer for canonical Market Intent States from Pack 2. The layer validates lineage, strict chronology, labels, metrics, data quality, future safety, prerequisite ordering, and the Version 1.0 frozen execution policy. It measures intent, direction, regime, and behaviour transitions; persistence; average intensity; intensity change; and continuation/reversal balance change. It has no parameter-update, trading-logic, broker, position, or order authority.

Execution remains `LOCKED_SIMULATION_ONLY`, direct execution remains false, live execution remains disabled, and order status remains `NO_ORDER_SENT`.

## Milestone Q Pack 4 — Market Intent Statistics ✅

- Added `afip/market_intent_statistics`.
- Aggregates accepted Pack 3 sequence reports into deterministic immutable research statistics.
- Calculates weighted persistence, weighted intent intensity, change rates, mean deltas, population standard deviation, pattern distribution, and dominant sequence pattern.
- Validates sample sufficiency, Pack 3 lineage, chronology, unique identifiers, count relationships, metric ranges, data quality, future safety, prerequisite ordering, and frozen policy.
- Broker remains XM Only; symbol remains GOLD# Only; base unit remains 0.01 lot.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, Production Certification, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Next: Milestone Q Pack 5 — Market Intent Stability Validation.

## Milestone Q Pack 5 — Market Intent Stability Validation ✅

- Added `afip/market_intent_stability_validation`.
- Validates accepted Pack 4 statistical windows for deterministic Market Intent stability.
- Measures weighted persistence and intensity means, metric ranges, dominant-pattern consistency, stable-window ratio, stability score, and stability band.
- Blocks insufficient samples, invalid Pack 4 lineage, duplicate IDs, overlapping chronology, invalid coverage, invalid metrics, unstable windows, uncertified data, future leakage, prerequisite-order violations, and frozen-policy violations.
- Broker remains XM Only; symbol remains GOLD# Only; base unit remains 0.01 lot.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, Production Certification, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Next: Milestone Q Pack 6 — Market Intent Drift Detection.

## Milestone Q Pack 6 — Market Intent Drift Detection ✅

- Added `afip/market_intent_drift_detection`.
- Detects deterministic drift across accepted Pack 5 stability-validation reports.
- Measures first-to-last persistence, intensity, stability-score, stable-window-ratio, and dominant-pattern-consistency deltas plus maximum adjacent score and intensity changes.
- Produces a deterministic drift score and NONE/LOW/MODERATE/HIGH drift band.
- Moderate or high drift requires research review but cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.
- Validates Pack 5 lineage, unique IDs, non-overlapping chronology, metric ranges, certified data, future safety, prerequisite ordering, and frozen policy.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Next: Milestone Q Pack 7 — Market Intent Confidence Calibration.

## Milestone Q Pack 7 — Market Intent Confidence Calibration ✅

- Added `afip/market_intent_confidence_calibration`.
- Calibrates deterministic research confidence from accepted Pack 6 Market Intent drift reports.
- Measures raw drift confidence, evidence coverage, persistence consistency, intensity consistency, stability consistency, pattern consistency, calibrated confidence, and confidence band.
- Blocks invalid Pack 6 lineage, duplicate drift IDs, chronology errors, detected or review-required drift, invalid metrics, uncertified data, future leakage, prerequisite-order violations, insufficient evidence, low confidence, and frozen-policy violations.
- Broker remains XM Only; symbol remains GOLD# Only; base unit remains 0.01 lot.
- Research only. No automatic parameter update, trading-logic change, production knowledge promotion, Production Certification, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Next: Milestone Q Pack 8 — Market Intent Validation Governance.

## Milestone Q Pack 8 — Market Intent Validation Governance
Status: COMPLETE

Added deterministic, immutable research governance for accepted Pack 7 Market Intent confidence calibration evidence. Production and execution authority remain disabled under AFIP Version 1.0 Feature Freeze.

## Milestone Q Pack 9 — Market Intent Review Certification ✅

- Added `afip/market_intent_review_certification`.
- Certifies accepted Pack 8 governance evidence for deterministic, immutable Market Intent research review.
- Validates Pack 8 lineage, unique IDs, chronology, governance acceptance, pending-review state, report sufficiency, governance score, data quality, future safety, prerequisite ordering, and frozen policy.
- READY marks evidence only as a Milestone Q completion candidate; it does not grant Production Certification or Release Candidate status.
- No automatic parameter update, trading-logic change, production knowledge promotion, position modification, broker request, or order transmission.
- Execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Next: Milestone Q Pack 10 — Market Intent Intelligence Complete.

## Milestone Q Pack 10 — Market Intent Intelligence Complete
- Status: COMPLETED
- Added deterministic, immutable Milestone Q completion from accepted Pack 9 review certificates.
- Enforces Pack 9 lineage, unique certificate IDs, chronology, review certification, completion-candidate status, sample sufficiency, review-score threshold, data quality, future safety, prerequisite order, and frozen execution policy.
- Milestone Q completion is research-only and does not grant Production Certification, Release Candidate status, production knowledge promotion, parameter updates, trading-logic changes, broker requests, position modification, or order transmission.
- Next milestone: Milestone R — Production Certification.
- Execution remains `LOCKED_SIMULATION_ONLY`; direct/live execution remain disabled; `NO_ORDER_SENT`.

## Milestone R Pack 1 — Production Regression Audit

Status: Implemented and validated.

- Added deterministic immutable Production Regression Audit runtime.
- Requires valid Milestone Q Pack 10 completion lineage.
- Audits targeted test suites and required repository validation checks.
- Validates evidence uniqueness, chronology, regression test-count continuity, and permanent trading/execution policy.
- Does not grant Production Certification or Release Candidate status.
- Execution remains `LOCKED_SIMULATION_ONLY`; direct/live execution stays disabled; `NO_ORDER_SENT`.
- Next: Milestone R Pack 2 — Duplicate Code Audit.

## Milestone R Pack 2 — Production Duplicate Code Audit

Status: Implemented and validated.

- Added `afip/production_duplicate_code_audit`.
- Audits reviewed duplicate-code evidence without modifying repository source.
- Requires valid Milestone R Pack 1 Regression Audit lineage.
- Classifies exact, structural, expected, and actionable duplication.
- Validates unique finding IDs, SHA-256 fingerprints, chronology, occurrence counts, review completion, duplicate ratio, severity, and frozen policy.
- Expected duplication is excluded from remediation totals only when explicitly classified and reviewed.
- Actionable findings are recorded for controlled Milestone R cleanup; this pack performs no refactor or deletion.
- Production Certification and Release Candidate status remain disabled.
- Execution remains `LOCKED_SIMULATION_ONLY`; direct/live execution remains disabled; `NO_ORDER_SENT`.

Next: Milestone R Pack 3 — Dead Code Audit.

## Milestone R Pack 3 — Production Dead Code Audit

Status: Implemented and validated.

- Added `afip/production_dead_code_audit`.
- Audits reviewed dead-code evidence without deleting source or changing runtime wiring.
- Requires valid Milestone R Pack 2 Duplicate Code Audit lineage.
- Classifies unreachable code, unused symbols, unused modules, obsolete paths, and policy-retained code.
- Validates unique finding IDs, SHA-256 fingerprints, chronology, review completion, dead-code ratio, severity, and frozen policy.
- Retained code is excluded from remediation only when explicitly classified, policy-retained, and reviewed.
- Actionable findings are recorded for controlled Milestone R cleanup; this pack performs no source removal.
- Production Certification and Release Candidate status remain disabled.
- Execution remains `LOCKED_SIMULATION_ONLY`; direct/live execution remains disabled; `NO_ORDER_SENT`.

Next: Milestone R Pack 4 — Architecture Audit.

## Milestone R Pack 4 — Production Architecture Audit

Status: Implemented and validated.

- Added `afip/production_certification_architecture_audit`.
- Audits reviewed architecture evidence without refactoring modules or changing runtime wiring.
- Requires valid Milestone R Pack 3 Dead Code Audit lineage.
- Classifies module-boundary violations, dependency-direction violations, dependency cycles, public API violations, policy violations, and accepted exceptions.
- Validates unique finding IDs, SHA-256 fingerprints, chronology, review completion, architecture score, severity, and frozen policy.
- Accepted exceptions are excluded from remediation only when explicitly classified and reviewed.
- Actionable findings are recorded for controlled Milestone R cleanup; this pack performs no architecture change.
- Production Certification and Release Candidate status remain disabled.
- Execution remains `LOCKED_SIMULATION_ONLY`; direct/live execution remains disabled; `NO_ORDER_SENT`.

Next: Milestone R Pack 5 — Repository Cleanup.

## Milestone R Pack 5 — Production Repository Cleanup

Status: Implemented and validated.

- Added `afip/production_repository_cleanup`.
- Validates controlled cleanup evidence after successful Milestone R Pack 4 Architecture Audit lineage.
- Classifies generated artifacts, cache artifacts, obsolete documents, stale test artifacts, and policy-retained artifacts.
- Requires unique cleanup IDs, SHA-256 fingerprints, valid chronology, completed review, authorized completion, and frozen-policy compliance.
- Blocks any cleanup authorization targeting protected source.
- Performs no trading-logic change, dependency rewiring, broker request, position modification, or order transmission.
- Production Certification and Release Candidate status remain disabled.
- Execution remains `LOCKED_SIMULATION_ONLY`; direct/live execution remains disabled; `NO_ORDER_SENT`.

Next: Milestone R Pack 6 — Safety Audit.

## Milestone R Pack 6 — Production Safety Audit

Status: Implemented and validated.

- Added `afip/production_certification_safety_audit` while preserving existing `afip.safety_audit`.
- Validates R Pack 5 Repository Cleanup lineage and reviewed controls across six mandatory safety domains.
- Enforces unique IDs, SHA-256 fingerprints, chronology, schema, review completion, domain coverage, safety score, and frozen policy.
- Blocks unaccepted or critical failures and performs no trading-logic change, safety bypass, broker request, position modification, or order transmission.
- Production Certification and Release Candidate remain disabled; execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Next: Milestone R Pack 7 — Security Audit.

## Milestone R Pack 7 — Production Security Audit

Status: Implemented and validated.

- Added `afip/production_certification_security_audit` without replacing existing security-related modules.
- Validates successful R Pack 6 Safety Audit lineage and reviewed controls across seven mandatory security domains.
- Enforces unique IDs, SHA-256 fingerprints, chronology, schema, review completion, domain coverage, security score, and frozen policy.
- Blocks unaccepted or critical failures, credential collection, secret exposure, dependency changes, network changes, broker requests, position modifications, and order transmission.
- Stores no credential or secret values and performs no trading-logic change.
- Production Certification and Release Candidate remain disabled; execution remains `LOCKED_SIMULATION_ONLY` / `NO_ORDER_SENT`.

Next: Milestone R Pack 8 — Data Integrity Audit.

## Milestone R Pack 8 — Production Data Integrity Audit
Status: Implemented and validated.
- Added `afip.production_certification_data_integrity_audit`.
- Validates R Pack 7 Security Audit lineage and seven mandatory data-integrity domains.
- Blocks invalid lineage, duplicate IDs, future evidence, schema defects, incomplete review, critical failures, low score, data rewrites, future leakage, and frozen-policy violations.
- Production Certification and Release Candidate remain disabled; execution remains locked.
Next: Milestone R Pack 9 — Performance Audit.

## Milestone R Pack 9 — Production Performance Audit
- Deterministic immutable performance evidence audit.
- Execution remains LOCKED_SIMULATION_ONLY; NO_ORDER_SENT.
- Next: Milestone R Pack 10 — Production Certification.

## Milestone R Pack 10 — Production Certification

Status: Implemented and validated.

- Added `afip.production_certification_final` as a deterministic immutable certification layer.
- Requires successful and complete evidence from Milestone R Packs 1–9.
- Validates required audit coverage, unique audit IDs, chronology, schema, pass status, critical blocks, score, and frozen execution policy.
- A passing result grants Production Certification only.
- Release Candidate and Version 1.0 Final remain ungranted.
- Direct/live execution remains disabled; execution remains `LOCKED_SIMULATION_ONLY`; `NO_ORDER_SENT`.

Validation: targeted 8 passed; full pytest 1735 passed; Local Quality Check PASS; Dashboard Build PASS.

Next: Release Candidate preparation under Milestone R.

## Milestone R Pack 11 — Release Candidate Preparation

Status: Implemented and validated.

- Added `afip.release_candidate_preparation` as a deterministic immutable preparation layer.
- Requires one valid Milestone R Pack 10 Production Certification record.
- Validates certification identity, chronology, schema, artifact manifest, validation manifest, bilingual documentation manifest, readiness score, and frozen execution policy.
- Passing Pack 11 prepares the repository for Release Candidate review only.
- Release Candidate and Version 1.0 Final remain ungranted.
- Execution remains `LOCKED_SIMULATION_ONLY`; direct/live execution disabled; `NO_ORDER_SENT`.

Next: Milestone R Pack 12 — Release Candidate Review.

## Milestone R Pack 12 — Release Candidate Review

Status: Implemented.

- Added `afip.release_candidate_review` as a deterministic immutable review layer.
- Requires one valid Pack 11 Release Candidate Preparation record.
- Validates preparation identity, chronology, schema, six required review domains, validation manifest, documentation manifest, score, and frozen execution policy.
- Passing Pack 12 grants Release Candidate status only.
- Version 1.0 Final remains ungranted.
- Execution remains `LOCKED_SIMULATION_ONLY`; direct/live execution disabled; `NO_ORDER_SENT`.

Next: Milestone R Pack 13 — Version 1.0 Final Review.

## Milestone R Pack 13 — Version 1.0 Final Review

Status: Implemented.

- Added `afip.version_1_final_review` as a deterministic immutable final-review layer.
- Requires one valid Pack 12 Release Candidate Review record.
- Validates Release Candidate identity, chronology, schema, eight final-review domains, validation manifest, documentation manifest, final score, and frozen execution policy.
- Passing Pack 13 grants AFIP Version 1.0 Final identity.
- Direct/live execution remains disabled; execution remains `LOCKED_SIMULATION_ONLY`; `NO_ORDER_SENT`.

Next: Version 1.0 Release Record.

## Milestone R Pack 14 — Version 1.0 Release Record

Status: Implemented.

- Added `afip.version_1_release_record` as a deterministic immutable release-record layer.
- Requires one valid Milestone R Pack 13 Version 1.0 Final Review record.
- Validates final-review identity, chronology, schema, validation evidence, bilingual documentation, release metadata, release score, and frozen execution policy.
- Passing Pack 14 records AFIP Version 1.0 Final.
- It does not authorize execution unlock, direct execution, live execution, broker requests, order transmission, or position modification.
- Execution remains `LOCKED_SIMULATION_ONLY`; `NO_ORDER_SENT`.

Next: Final repository snapshot and Git tag `v1.0.0` after local validation.

## Milestone S Pack 1 — Locked Simulation Runtime Runner

- Added continuous operational runner command: `python afip.py run-locked-simulation`.
- Default interval: 60 seconds; optional finite cycle count for controlled validation.
- Added immutable execution guards: LOCKED_SIMULATION_ONLY, Direct Execution False, Live Execution False, NO_ORDER_SENT.
- Added JSONL event ledger, atomic status record, acceptance summary, duplicate snapshot fingerprinting, cycle-failure isolation, dashboard rebuild hook, and graceful Ctrl+C shutdown.
- No trading logic, broker order path, risk policy, profile policy, or position lifecycle was changed.

## Milestone S Pack 2 — Four-Profile Demo Operational Configuration
- Added isolated operational configuration for P1 High Safety, P2 Balanced, P3 High Risk Within Plan, and P4 Research.
- XM-only and GOLD#-only validation is mandatory.
- Every profile remains `LOCKED_SIMULATION_ONLY`; direct and live execution are false; order status is `NO_ORDER_SENT`.
- Per-profile MT5 folders, terminals, servers, runtime, database, logs, dashboard, learning, knowledge, and statistics paths are isolated.
- Duplicate path and configured-account protection runs before startup.
- Credentials are environment-only and are not stored in repository files.
- Dashboard includes a four-profile operational overview.

## Milestone S Pack 3 — MT5 Multi-Terminal Connection Manager
- Isolated sequential MT5 health verification for P1–P4.
- Exact terminal/login/server mapping with account and server mismatch protection.
- GOLD# Market Watch and tick verification.
- Bounded reconnect attempts and per-profile health snapshots.
- Dashboard MT5 status, latency, reconnect count and readable reason.
- Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.

## Milestone S Pack 4 — Demo Execution Gateway
- Added demo-only broker execution gateway for P1–P4.
- Real and contest MT5 accounts are blocked by mandatory `trade_mode=DEMO` verification before `order_send`.
- Added exact account/server, XM, GOLD#, trade permission, real-data, risk, cost, protected SL/TP, manual override, allocation, and duplicate-cooldown gates.
- Fixed unit size remains 0.01; profiles allocate up to three separate units according to capital-per-unit and confidence policy.
- Added environment-only two-level local arming and immediate disarm scripts.
- Validation never arms execution and never transmits an order.

## Milestone S Pack 4.1 — Live Dashboard Runtime Wiring
- Added P1-P4 operational cards at the top of the dashboard.
- Dashboard reads demo runtime PID, MT5 health, demo gateway state, waiting reason, confidence, orders, tickets, timestamps, and freshness from isolated profile runtime files.
- Added continuous dashboard regeneration service with five-second browser refresh.
- Trading logic and demo execution policy remain unchanged.

## Milestone S Pack 4.2 — Demo Execution Trading Cost Contract Recovery
- Corrected the verified contract mismatch between Trading Cost Intelligence and Demo Execution Gateway.
- `CAUTION` remains executable only when the authoritative `allowed` field is `True`.
- `BLOCK`, unknown status, missing permission, and inconsistent contracts remain fail-closed.
- Added execution diagnostics for spread thresholds, point size, digits, MT5 order-check/send calls, and MT5 result information.
- No trading, confidence, spread, sizing, arming, account, or broker safety threshold was weakened.
- Validation: 13 pack tests, 15 combined pack/dashboard tests, and 1808 full tests passed in the source repository.

## Milestone S Pack 4.6 — Capital Growth Table Safety Correction
- Replaced linear capital-per-unit interpretation for P1/P2 with explicit capital-tier allocation tables.
- P1 tiers culminate at USD 7,200 with maximum concurrent allocation 0.03 + 0.03 + 0.03 + 0.03.
- P2 tiers culminate at USD 7,800 with maximum concurrent allocation 0.03 + 0.03 + 0.03 + 0.03.
- Balances above the final tier do not increase risk; excess profit is available for operator withdrawal policy.
- P3/P4 remain fixed 0.01 research allocation per approved distinct signal, without a profile capital-tier ceiling; all safety gates remain active.

## Milestone S Pack 4.7 — Backward-Compatible Capital Allocation Recovery
- Corrected `DemoProfilePolicy.validate()` control flow so `LEGACY_FIXED_UNIT`, `CAPITAL_TIER_TABLE`, and `RESEARCH_FIXED_001` are all recognized deterministically.
- Preserved the approved capped P1/P2 capital-tier tables from Pack 4.6.
- Restored compatibility report fields: `order_unit_distribution`, `maximum_orders`, and `remaining_order_capacity`.
- No changes to confidence, risk, spread, cooldown, demo verification, manual override, SL/TP, or MT5 order safety.
- Validation: Pack regression 17 passed; full regression 1812 passed.

## Milestone S Pack 4.8 — Capital Growth Engine and Operator Visibility
- Extracted deterministic P1/P2 capital-tier lookup from the demo execution gateway into `afip.capital_growth_engine`.
- Preserved `LEGACY_FIXED_UNIT`, `CAPITAL_TIER_TABLE`, and `RESEARCH_FIXED_001` gateway compatibility.
- Added current tier, next tier, amount remaining, maximum tier, and withdrawal-reference diagnostics to demo runtime state.
- Added live P1–P4 dashboard rows for balance, tier allocation, next-tier progress, and withdrawal reference.
- Corrected Pack runner usage to invoke pytest through the active Python interpreter instead of a relocatable-broken `pytest.exe` launcher.
- Trading thresholds, risk approval, trading-cost approval, cooldown, manual override, SL/TP, and MT5 order transmission behavior remain unchanged.

## Milestone S Pack 5.1 — Research Data Foundation
- Added versioned unified research contract `AFIP-RESEARCH-DATA-1.0`.
- Added read-only ledger ingestion for Decision Gate and Order Execution events.
- Added atomic Trade Case Files and UTC/SHA-256 data lineage.
- Added pending M30/H1/H4/D1 checkpoint schedules with future-data leakage protection metadata.
- Added idempotent ingestion and malformed-line quarantine.
- Trading logic and MT5 execution path remain unchanged.

## Milestone S Pack 5.2 — Trade Case Complete & Historical Research Foundation

Status: IMPLEMENTED (Patch Only)

- Extended the Pack 5.1 research contract with M15/M30/H1/H4/D1 post-trade checkpoints.
- Added complete research-only trade lifecycle updates for PASS/WAIT/BLOCK gates, holding observations, exit quality, retained/given-back profit, and post-trade assessment.
- Added deterministic candle-close replay queue, cursor, progress, event ledger, and statistics with explicit future-data-leakage blocking.
- Added permanent Dashboard Research Foundation panel near the bottom, including historical coverage, replay state, dataset counts, Top 100 pattern statistics, and similar-pattern monitor.
- Similarity and historical research remain read-only and cannot affect execution, thresholds, safety gates, position sizing, or trading decisions.
- AFIP Gold Ultimate (V2) remains locked for future development.
