# Validation Guide — Milestone S Pack 4

```powershell
.\RUN_MILESTONE_S_PACK_4.ps1
```

Expected:

- Pack tests pass.
- Full pytest passes.
- Local Quality Check passes.
- All selected MT5 profiles connect.
- Demo gateway status can be read.
- No validation command arms or transmits an order.

Operational arming must be performed separately with `SET_AFIP_DEMO_EXECUTION_ARM_LOCAL.ps1`.
