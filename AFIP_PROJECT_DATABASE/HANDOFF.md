# AFIP Handoff

## Current work
Production Bring-up Pack 10 — Production Certification

## Base
- User-verified GitHub commit before queued patches: `826552a`
- Packs 5 through 9 must be installed and validated before Pack 10.
- Apply queued patches in numerical order.

## Pack 10 scope
- Read-only certification of Production Bring-up Packs 1–9
- Deterministic component and Version 1 policy checks
- Bilingual certification summary and next action
- Dashboard certification panel without navigation changes
- Market Intelligence readiness gate

## Policy
- Broker: XM only
- Symbol: GOLD# only
- Live execution: disabled
- Execution: LOCKED_SIMULATION_ONLY
- Patch only and backward compatible
- No trading decision or order-placement logic changed

## Validation order
1. Install queued Packs 5–10 in order.
2. Run targeted Pack 10 tests.
3. Run full pytest.
4. Run AFIP Local Quality Check.
5. Generate and inspect the dashboard certification panel.
6. Commit and push only after all checks pass.

## Next work
Milestone I Pack 1 — Economic Calendar Intelligence

## Milestone I Pack 0 — Profile Customization Completion
- Custom naming, preset copy, editing, activation, duplication, archive, delete, and account assignment
- Atomic JSON persistence with version history
- Dashboard EN/TH profile customization explainability
- Profile remains separate from Account and MT5
- Live execution disabled; trading logic unchanged
- Next: Milestone I Pack 1 Economic Calendar Intelligence

- Quality result: targeted 6 passed; full pytest 1012 passed; Local Quality Check PASS; Dashboard PASS.

## Milestone I Pack 1 — Economic Calendar Intelligence
- Structured impact, gold relevance, category, countdown, and event-window intelligence
- Dashboard explanations in English and Thai
- Economic events never execute orders directly
- XM only, GOLD# only, live execution disabled
- Next: Milestone I Pack 2 News Intelligence

## Milestone I Pack 2 — News Intelligence
- Deterministic structured news classification
- Source reliability and normalized duplicate detection
- Reliability-weighted aggregate sentiment
- Dashboard explanations in English and Thai
- News never executes orders directly
- Next: Milestone I Pack 3 Gold Macro Intelligence

## Milestone I Pack 3 — Gold Macro Intelligence
Patch adds deterministic CPI, PPI, employment, GDP, PMI and ISM classification for XM GOLD# with bilingual Dashboard explainability. Macro data is context only and cannot execute orders. Expected full suite: 1030 passed. Next: Milestone I Pack 4 Central Bank Intelligence.

## Milestone I Pack 4 — Central Bank Intelligence
- Deterministic FOMC, ECB, BOE, BOJ, and PBOC policy/speech classification
- Hawkish, dovish, and neutral policy bias with structured GOLD# context
- Dashboard explanations in English and Thai
- Central-bank information never executes orders directly
- XM only, GOLD# only, live execution disabled
- Expected full pytest: 1036 passed
- Next: Milestone I Pack 5 COT Intelligence


## Milestone I Pack 5 — COT Intelligence
- Added deterministic Commercial and Non-Commercial positioning analysis.
- Added net position, weekly change, positioning trend, and bilingual dashboard explainability.
- COT data is structured context only; direct execution remains prohibited.
- Expected full suite after patch: 1042 passed.
- Next: Milestone I Pack 6 — Open Interest Intelligence.

## Milestone I Pack 6 — Open Interest Intelligence
- Added deterministic futures OI and price-relationship analysis.
- Added participation expansion/contraction, market interpretation, and bilingual dashboard explainability.
- Open-interest data is structured context only; direct execution remains prohibited.
- Expected full suite after patch: 1048 passed.
- Next: Milestone I Pack 7 — ETF Flow Intelligence.

## Milestone I Pack 7 — ETF Flow Intelligence
- Status: completed in patch build
- Scope: GLD, IAU, and gold ETF daily/weekly flow and holdings-change context
- Policy: XM only, GOLD# only, live execution disabled, direct execution false
- Dashboard: bilingual English/Thai ETF Flow Intelligence panel
- Next: Milestone I Pack 8 USD Index Intelligence

## Milestone I Pack 8 — USD Index Intelligence
- Added deterministic DXY trend, GOLD# correlation, and divergence analysis.
- Added aggregate USD trend, structured gold effect, and bilingual Dashboard explainability.
- USD index data is structured context only; direct execution remains prohibited.
- Expected full suite after patch: 1060 passed.
- Next: Milestone I Pack 9 — Bond Yield Intelligence.

## Milestone I Pack 9 — Bond Yield Intelligence
- Added deterministic US2Y, US10Y, real-yield, and yield-curve analysis.
- Added structured GOLD# effect and bilingual Dashboard explainability.
- Yield data is context only; direct execution remains prohibited.
- Expected full suite after patch: 1066 passed.
- Next: Milestone I Pack 10 — Market Regime V2.


## Milestone I Pack 10 — Market Regime V2
- Aggregates Economic Calendar, News, Gold Macro, Central Bank, COT, Open Interest, ETF Flow, USD Index, and Bond Yield intelligence.
- Produces explainable regime, directional bias, risk state, component alignment, confidence, and next review time.
- Direct execution remains prohibited; live execution remains disabled.
- Expected full suite after patch: 1072 passed.
- Milestone I patch sequence complete, pending user validation in numerical order.

## Milestone J Pack 1 — Decision Intelligence Foundation
- Deterministic consensus and conflict resolution after Market Regime V2
- Weighted explainable evidence in English and Thai
- XM / GOLD# only; live and direct execution remain disabled
- Next: Milestone J Pack 2 — Consensus Engine


## Milestone J Pack 2
Consensus Engine added with bilingual explainability. Direct execution remains disabled.

## Current Handoff — Milestone J Pack 5
Trade Scoring Engine completed. Continue with Milestone J Pack 6 Unit Allocation Engine. Live execution remains disabled.
