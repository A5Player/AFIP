$ErrorActionPreference = 'Stop'
Write-Host '📡 AFIP Dashboard Live Service — MT5 P1-P4 + Runtime + Research'
& .\.venv\Scripts\python.exe .\tools\afip_dashboard_live_mt5.py --root . --interval-seconds 10
exit $LASTEXITCODE
