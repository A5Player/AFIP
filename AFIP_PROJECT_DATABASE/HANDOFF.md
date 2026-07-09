# AFIP Handoff

Current stage: Production Milestone H Pack 5 — Historical Data Download and Quality Pipeline.

Latest completed baseline before this patch:
- Version 1 Production Freeze completed.
- Milestone H Pack 1 Dashboard Foundation completed.
- Milestone H Pack 2 Configuration Center completed.
- Milestone H Pack 3 Profile Manager, Setup Wizard, Connection Manager, Historical Data Manager, and Dashboard Runtime completed.
- Milestone H Pack 4 Runtime Service Manager, VPS Watchdog, Recovery Engine, and Event Logger completed.

Pack 5 adds:
- Historical Data Download Pipeline.
- M1, M5, M15, H1, H4, and D1 download planning.
- Missing bar, duplicate bar, and invalid bar validation.
- Historical data quality score.
- Walk Forward readiness gate.
- Research readiness gate.
- Paper Trading readiness gate.
- Research statistics separated from Live statistics.
- Dashboard Runtime historical download dependency.

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
- Pack 5 test: 7 passed expected.
- Full pytest expected after patch: 908 passed.
- AFIP Local Quality Check must remain PASS.

Safety notes:
- No trading logic changed.
- Live execution remains disabled.
- Historical download prepares data only.
- Research and Live statistics remain separated.
- Market regime remains required before signal context.

Next recommended pack:
- H6 Research Center for separated Research, Demo, and Live analytics and Top 10 statistics.

## Production Milestone H Pack 6 — Research Center

Status: Completed as patch.

Added Research Center runtime with separated Research and Live statistics, dashboard-ready Top 10 analytics, and Standard Learning candidate gate. Live execution remains disabled. Trading logic was not changed.

Validation:

- Pack test: 7 passed
- Full pytest: 915 passed
- AFIP Local Quality Check: PASS

Next recommended pack: Milestone H Pack 7 — Paper Trading Runtime and Order Timeline Explainability.
