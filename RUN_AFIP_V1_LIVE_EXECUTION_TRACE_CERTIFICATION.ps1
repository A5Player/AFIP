param([string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
& $python -m pytest `
  tests\test_afip_v1_execution_batch_preflight_certification.py `
  tests\test_afip_v1_live_execution_trace_certification.py `
  -vv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "AFIP V1 Live Execution Trace focused certification: PASS"
