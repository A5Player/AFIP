# AFIP Handoff

Current stage: Production Milestone H Pack 3 — Profile Manager, Setup Wizard, Connection Manager, Historical Data Manager, Dashboard Runtime.

Latest completed baseline before this patch:
- Version 1 Production Freeze completed.
- Milestone H Pack 1 Dashboard Foundation completed.
- Milestone H Pack 2 Configuration Center completed.

Pack 3 adds:
- Profile Manager for reusable trading policy profiles.
- Setup Wizard for first VPS setup flow.
- Connection Manager for Internet, MT5, broker, market, session, and system status.
- Historical Data Manager for missing bar, duplicate bar, quality, Walk Forward, and Research readiness.
- Dashboard Runtime Status composer for H Pack 3 manager readiness.

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

Quality result:
- Pack 3 test: 7 passed.
- Milestone H Pack 1-3 tests: 19 passed.
- Full pytest: 894 passed.
- AFIP Local Quality Check: PASS.

Safety notes:
- No trading logic changed.
- Live execution is blocked in this pack.
- Market regime remains required before signal context.
- Dashboard explainability sections are prepared for waiting, entry, holding, stop loss movement, trailing stop, break even, partial close, final close, rejected decisions, alternative decisions, and current AI reasoning.

Next recommended pack:
- H4 Dashboard Intelligence Detail Rows and Order Center Explainability.
