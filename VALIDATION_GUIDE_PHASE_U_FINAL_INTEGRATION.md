# Validation Guide — Phase U Final Integration

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\VALIDATE_PHASE_U_FINAL.ps1
.\RUN_AFIP_FINAL_RESEARCH.ps1
```

Required evidence:
- Phase U tests pass
- Local Quality PASS
- `runtime/research/final_research_run.json` exists
- final report does not claim execution authority
- unavailable sources remain `DATA_UNAVAILABLE`, `TIMEOUT`, or explicit error states
