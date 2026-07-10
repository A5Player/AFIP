# Milestone K Pack 7 — Partial Close Intelligence

## Scope
Adds deterministic, simulation-only partial-close review for XM GOLD# positions.

## Controls
- 1 Unit remains exactly 0.01 lot.
- Partial close is expressed in whole Units only.
- At least the configured minimum runner Units must remain open.
- BUY and SELL profit direction is validated.
- Profit, trading cost, risk, timing, and market structure must pass.
- Direct execution and live execution remain disabled.
- Every result remains `NO_ORDER_SENT` and `LOCKED_SIMULATION_ONLY`.

## Dashboard
Adds English/Thai explainability for readiness, approved Units, runner Units, estimated realized profit, holding reason, partial-close reason, next action, confidence, and next review time.

## Validation
```powershell
pytest tests/test_milestone_k_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone K Pack 7 Partial Close Intelligence"
git push
```
