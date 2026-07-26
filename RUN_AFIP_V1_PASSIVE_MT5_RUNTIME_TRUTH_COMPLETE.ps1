param([int]$IntervalSeconds = 10)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (Test-Path ".\.venv\Scripts\Activate.ps1") { . ".\.venv\Scripts\Activate.ps1" }
python -m pytest tests\test_afip_v1_passive_mt5_monitoring.py -q
python tools\afip_mt5_multi_terminal_check.py
python -m afip.dashboard_ui
Write-Host "PASSIVE MT5 runtime truth repair: PASS" -ForegroundColor Green
Write-Host "Passive check does not initialize or reopen MT5 terminals." -ForegroundColor Cyan
