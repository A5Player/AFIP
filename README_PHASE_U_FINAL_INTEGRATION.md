# AFIP Phase U Final Integration

This release adds a bounded one-shot research orchestrator. It prevents an MT5/provider stall from holding the PowerShell session forever and writes an auditable final-run report.

## Run

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_AFIP_FINAL_RESEARCH.ps1
```

Default limits:
- research collector: 900 seconds
- dashboard generation: 180 seconds

Override example:

```powershell
.\RUN_AFIP_FINAL_RESEARCH.ps1 -CollectorTimeoutSeconds 1200
```

The run remains research-only and has no execution authority.
