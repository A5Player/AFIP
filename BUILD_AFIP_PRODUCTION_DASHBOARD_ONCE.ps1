$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "[1/2] Refreshing MT5 P1-P4 account snapshots..."
& .\.venv\Scripts\python.exe -u .\tools\afip_mt5_multi_terminal_check.py --config .\config\four_profile_demo.json --reconnect-attempts 0
if ($LASTEXITCODE -ne 0) { Write-Warning "One or more MT5 profiles are not connected. Dashboard will show the exact reason." }
Write-Host "[2/2] Building four-page dashboard..."
& .\.venv\Scripts\python.exe -u -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed." }
Start-Process .\runtime\dashboard\afip_dashboard.html
