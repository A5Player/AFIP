# Milestone K Pack 3 — Smart Exit Engine

Adds deterministic, explainable, simulation-only exit planning for XM / GOLD#.

Supported actions:
- HOLD
- PARTIAL_CLOSE
- EXIT

The runtime validates open units, fixed unit policy, price context, risk, timing, trading cost, and execution policy. It never changes a live position and always returns `NO_ORDER_SENT` behavior.

Run:
```powershell
.\RUN_MILESTONE_K_PACK_3.ps1
```
