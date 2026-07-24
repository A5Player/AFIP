param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
if (Test-Path ".\.venv\Scripts\Activate.ps1") { . ".\.venv\Scripts\Activate.ps1" }

Write-Host "[1/6] Stop AFIP and stale execution workers"
if (Test-Path ".\STOP_AFIP.ps1") { .\STOP_AFIP.ps1 }
python -m tools.afip_demo_execution_control stop-all

Write-Host "[2/6] Compile repaired runtime"
python -m py_compile afip\demo_execution_gateway\runtime.py tools\afip_profile_execution_once.py

Write-Host "[3/6] Focused regression"
python -m pytest -q tests\test_afip_v1_runtime_execution_repair_pack_1.py tests\test_afip_final_execution_ownership.py

Write-Host "[4/6] Verify isolated MT5 bindings"
python -m tools.afip_verify_account_isolation --config config\four_profile_demo.json --output runtime\account_isolation_status.json
if ($LASTEXITCODE -ne 0) { throw "Account isolation verification failed. AFIP remains stopped." }

Write-Host "[5/6] Start sequential execution router"
python -m tools.afip_demo_execution_control start-all
if ($LASTEXITCODE -ne 0) { throw "AFIP start failed." }

Write-Host "[6/6] Show status"
Start-Sleep -Seconds 8
python -m tools.afip_demo_execution_control status
Write-Host "AFIP is running only if router.running=true and each enabled profile shows the expected account/terminal binding."
