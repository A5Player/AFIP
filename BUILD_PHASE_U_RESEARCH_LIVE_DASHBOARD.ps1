$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }
& $python tools\afip_research_live_dashboard.py --root .
exit $LASTEXITCODE
