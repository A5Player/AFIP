# AFIP Version 1.0 Final Integration

This Patch Only pack adds one final integration authority over the latest repository without replacing trading logic, research logic, risk controls, or historical datasets.

## Final architecture

- **Trading Runtime**: existing `tools.afip_demo_execution_control` and production execution modules.
- **Research Runtime**: existing Phase V / Automatic Research / Historical Replay / Runtime Observatory stack.
- **Unified Dashboard**: `runtime/dashboard/afip_dashboard.html`, generated from canonical runtime snapshots.
- **Single Operations Interface**: `START_AFIP.ps1`, `STOP_AFIP.ps1`, `STATUS_AFIP.ps1`.
- **Historical Data Lake**: `runtime/research/historical_data_lake`.
- **Incremental File Index**: `runtime/research/research_file_index.json`.

Legacy scripts remain for backward compatibility but are classified as compatibility entry points. New operations should use the three final scripts only.

## Install

```powershell
cd <extracted-pack>
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_FINAL_INTEGRATION.ps1 -ProjectRoot C:\AFIP\source
cd C:\AFIP\source
.\RUN_AFIP_V1_FINAL_INTEGRATION.ps1
```

Use `-FullRegression` only after the targeted validation succeeds.
