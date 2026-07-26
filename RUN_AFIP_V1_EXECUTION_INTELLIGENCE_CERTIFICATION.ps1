param(
  [string]$ProjectRoot = "C:\AFIP"
)
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
& $Python -m pytest -q `
  tests\test_afip_v1_execution_batch_preflight_certification.py `
  tests\test_afip_v1_live_execution_trace_certification.py `
  tests\test_afip_v1_execution_intelligence_certification.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "AFIP V1 Execution Intelligence focused certification: PASS"
