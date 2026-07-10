# AFIP Handoff

## Current work
Production Bring-up Pack 9 — Runtime Supervisor

## Base
- User-verified GitHub commit before queued patches: `826552a`
- Packs 5 through 8 must be installed and validated before Pack 9.
- Apply queued patches in numerical order.

## Pack 9 scope
- Read-only runtime health aggregation
- Healthy, warning, and critical dependency counts
- Bilingual recovery guidance and next review explanation
- Supervisor confidence
- Dashboard panel integration without navigation changes

## Policy
- Broker: XM only
- Symbol: GOLD# only
- Live execution: disabled
- Execution: LOCKED_SIMULATION_ONLY
- Patch only and backward compatible
- No trading decision or order-placement logic changed

## Validation order
1. Run targeted Pack 9 tests.
2. Run full pytest.
3. Run AFIP Local Quality Check.
4. Generate the dashboard.
5. Verify the Runtime Supervisor panel.
6. Commit and push only after all checks pass.

## Next work
Production Bring-up Pack 10 — Production Certification
