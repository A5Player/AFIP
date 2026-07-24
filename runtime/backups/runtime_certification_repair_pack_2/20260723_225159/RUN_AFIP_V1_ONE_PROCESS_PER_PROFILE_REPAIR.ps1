$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "AFIP venv not found: $Python" }

Write-Host "[1/5] Stop old AFIP router and workers"
& $Python -m tools.afip_demo_execution_control stop-all | Out-Host

Write-Host "[2/5] Compile repaired runtime files"
& $Python -m py_compile `
  tools\afip_demo_execution_control.py `
  tools\afip_profile_sequential_execution_router.py `
  tools\afip_profile_execution_worker.py `
  tools\afip_profile_execution_once.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/5] Run focused regression"
& $Python -m pytest tests\test_afip_v1_one_process_per_profile_repair.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/5] Start one persistent process per profile"
& $Python -m tools.afip_demo_execution_control start-all | Out-Host
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Start-Sleep -Seconds 12
Write-Host "[5/5] Show authoritative status"
& $Python -m tools.afip_demo_execution_control status | Out-Host
