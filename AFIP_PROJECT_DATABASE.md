
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
