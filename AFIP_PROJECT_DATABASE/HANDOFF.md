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
