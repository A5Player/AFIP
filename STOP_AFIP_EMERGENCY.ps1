$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
Write-Host 'Stopping AFIP sequential execution router and all legacy profile workers...' -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m tools.afip_demo_execution_control stop-all
Write-Host 'Execution stopped. Existing MT5 positions were not closed.' -ForegroundColor Green
