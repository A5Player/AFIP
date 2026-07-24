# AFIP V1 Control Center Pack 1

Baseline: `f471f2c`.

This patch adds a passive Control Center and startup-status schema through the existing `DashboardAuthority`. It does not create an execution gateway, does not start research synchronously, and does not modify execution authority.

## Install

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
cd C:\AFIP_V1_CONTROL_CENTER_PACK_1
.\INSTALL_AFIP_V1_CONTROL_CENTER_PACK_1.ps1 -ProjectRoot C:\AFIP\source
```

## Validate

```powershell
.\RUN_AFIP_V1_CONTROL_CENTER_PACK_1.ps1 -ProjectRoot C:\AFIP\source
```

## Full regression

```powershell
cd C:\AFIP\source
.\.venv\Scripts\python.exe -m pytest -q
```

Generated page: `runtime/dashboard/afip_control_center.html`.

Rollback from the timestamped backup under `runtime/backups/control_center_pack_1/` by copying backed-up files to their original relative paths. Files that did not previously exist may be removed individually; do not delete the repository or runtime/research data.
