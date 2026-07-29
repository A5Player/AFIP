param([string]$ProjectRoot = 'C:\AFIP')
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = 'python' }
& $Python -m pytest tests\test_afip_v1_runtime_truth_authority_repair.py -v
if ($LASTEXITCODE -ne 0) { throw "Focused test failed: $LASTEXITCODE" }
& $Python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed: $LASTEXITCODE" }
Write-Host 'Runtime Truth Authority Repair focused certification: PASS'
Write-Host 'Start runtime with .\START_AFIP.ps1 -ProjectRoot C:\AFIP, then allow the dashboard monitor to refresh.'
