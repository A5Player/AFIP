# AFIP Milestone S Cleanup Pack 4.2.1

Documentation financial naming hotfix only.

## Scope

- Replaces the prohibited non-financial term in the three Pack 4.2 documentation files.
- Runs Financial Naming Validation.
- Runs the affected Pack 4.2 and Confidence Calibration regression tests.
- Does not modify trading runtime, confidence thresholds, allocation, RR portfolio, TP, SL, or execution state.
- Execution remains stopped.

## Run

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process Bypass -Force
.\RUN_MILESTONE_S_CLEANUP_PACK_4_2_1.ps1
```

After it passes:

```powershell
.\.venv\Scripts\python.exe -m pytest
```
