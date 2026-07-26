$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m pytest
python tools\afip_mt5_multi_terminal_check.py
python -m afip.dashboard_ui
Start-Process (Join-Path $PSScriptRoot 'runtime\dashboard\afip_dashboard.html')
