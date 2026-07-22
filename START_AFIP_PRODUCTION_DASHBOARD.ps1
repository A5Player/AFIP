$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "AFIP Production Dashboard - MT5 P1-P4 Live Snapshot + 4 Pages"
& .\.venv\Scripts\python.exe -u .\tools\afip_dashboard_live.py --root . --interval 10
