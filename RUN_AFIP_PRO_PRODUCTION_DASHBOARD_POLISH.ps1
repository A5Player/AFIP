param([Parameter(Mandatory=$false)][string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
& $Python -m pytest tests\test_afip_pro_production_dashboard_polish.py tests\test_afip_pro_final_financial_dashboard_authority.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "AFIP Pro production dashboard polish: PASS"
Write-Host "Dashboard rebuilt. Runtime and MT5 were not started."
