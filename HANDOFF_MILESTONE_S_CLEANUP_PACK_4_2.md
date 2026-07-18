# Handoff — Milestone S Cleanup Pack 4.2

## Starting evidence

User full regression:
- 1855 collected
- 1853 passed
- 2 failed

Residual failures:
1. Financial naming validation: non-financial term `Protection Control` in `README_MILESTONE_S_PACK_4_9_TH.md`.
2. Legacy confidence-calibration simulation expected `SIMULATION_ORDER_READY` at confidence 85 after risk approval, but Pack 4.1 normal execution threshold returned `NO_ORDER`.

## Repair decision

Do not weaken the P1-P3 98+ execution threshold. Add a narrowly scoped compatibility policy only inside `ConfidenceCalibrator` for risk-approved legacy `SIMULATION` decisions below 98. The builder requires all compatibility markers and risk approval before allowing exactly one unit.

## Safety invariants

- Direct builder confidence below 98 remains blocked.
- Failed risk cannot be bypassed.
- Excessive spread remains blocked.
- P1-P3 Demo Execution threshold is unchanged.
- Execution remains stopped.

## Validation performed against source snapshot

Focused target set: 8 passed.
Full available snapshot regression after removing temporary payload/cache: 1841 passed.
The user's production checkout contains additional tests; run the commands below there for final certification.

## Next commands

```powershell
cd C:\AFIP
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe tools\afip_local_quality_check.py
```

