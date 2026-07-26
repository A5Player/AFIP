$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pytest tests\test_afip_v1_dashboard_runtime_truth_freshness_repair.py -q
python tools\afip_mt5_multi_terminal_check.py
python -m afip.dashboard_ui
Write-Host "AFIP V1 Dashboard Runtime Truth & Freshness Repair: PASS"
Write-Host "Open: runtime\dashboard\afip_dashboard.html"
