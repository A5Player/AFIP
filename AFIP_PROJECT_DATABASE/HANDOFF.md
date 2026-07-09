# AFIP Handoff

Current stage: Production Milestone H Pack 4 — Runtime Service Manager for Windows VPS operation.

Latest completed baseline before this patch:
- Version 1 Production Freeze completed.
- Milestone H Pack 1 Dashboard Foundation completed.
- Milestone H Pack 2 Configuration Center completed.
- Milestone H Pack 3 Profile Manager, Setup Wizard, Connection Manager, Historical Data Manager, and Dashboard Runtime completed.

Pack 4 adds:
- Runtime Service Manager for deterministic VPS runtime readiness.
- Runtime Recovery Engine for Internet, MT5, and broker recovery explainability.
- Runtime Event Logger for dashboard timeline history.
- Runtime heartbeat and watchdog review status.
- Dashboard Runtime integration with runtime service dependency.

Architecture decisions preserved:
- Profile is not Account.
- Profile is not MT5.
- Profile is not Demo or Real.
- One Profile can be assigned to any account.
- One account can switch Profiles.
- Broker remains XM only for Version 1.
- Symbol remains GOLD# only for Version 1.
- Multi broker remains disabled for Version 1.
- 1 Unit = 0.01 lot.
- AFIP increases Unit count, not direct lot size.

Quality target:
- Pack 4 test: 7 passed expected.
- Full pytest expected after patch: 901 passed.
- AFIP Local Quality Check must remain PASS.

Safety notes:
- No trading logic changed.
- Live execution remains disabled.
- Runtime recovery pauses trading before reconnection checks.
- Dashboard must show waiting reason and expected next action.
- Market regime remains required before signal context.

Next recommended pack:
- H5 Historical Data Download and Quality Pipeline for Walk Forward and Research datasets.
