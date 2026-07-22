$ErrorActionPreference = 'Stop'
Write-Host '📊 AFIP Dashboard — Live MT5 Snapshot + Four Pages'
& .\.venv\Scripts\python.exe .\tools\afip_dashboard_live_mt5.py --root . --once
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Start-Process .\runtime\dashboard\afip_dashboard.html
