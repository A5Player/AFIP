$ErrorActionPreference = "Stop"
Set-Location C:\AFIP
python -m pytest
python -m afip.dashboard_ui
Start-Process (Resolve-Path "runtime\dashboard\afip_unified_dashboard.html")
