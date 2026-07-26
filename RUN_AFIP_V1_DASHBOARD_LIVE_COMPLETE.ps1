param([int]$IntervalSeconds = 10)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python tools\afip_mt5_multi_terminal_check.py
python -m afip.dashboard_ui
Start-Process (Join-Path $PSScriptRoot "runtime\dashboard\afip_dashboard_completeness.html")
Write-Host "Starting read-only live dashboard refresh every $IntervalSeconds seconds. Press Ctrl+C to stop."
python -m afip.dashboard_ui --live $IntervalSeconds
