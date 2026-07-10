# AFIP Handoff

## Current work
Production Bring-up Pack 8 — Dashboard Live Runtime

## Base
- User-verified GitHub commit before queued patches: `826552a`
- Pack 5, Pack 6, and Pack 7 must be installed and validated before Pack 8.
- Patch delivery is incremental and must be applied in order.

## Pack 8 scope
- Read-only dashboard refresh readiness
- Snapshot freshness and sequence visibility
- Dependency readiness
- Bilingual waiting reason and expected next action
- Dashboard panel integration

## Policy
- Broker: XM only
- Symbol: GOLD# only
- Live execution: disabled
- Execution: LOCKED_SIMULATION_ONLY
- Patch only and backward compatible
- No trading decision or order placement logic changed

## Validation order
1. Run targeted Pack 8 tests.
2. Run full pytest.
3. Run AFIP Local Quality Check.
4. Generate the dashboard.
5. Verify the Dashboard Live Runtime panel.
6. Commit and push only after all checks pass.

## Next work
Production Bring-up Pack 9 — Runtime Supervisor
