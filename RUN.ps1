param(
  [string]$ProjectRoot = "C:\AFIP\source"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Python venv not found: $Python" }

& $Python -m py_compile `
  afip\demo_execution_gateway\runtime.py `
  tools\afip_profile_sequential_execution_router.py `
  tools\afip_demo_execution_control.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m pytest -q `
  tests\test_afip_v1_runtime_certification_repair_pack_2.py `
  tests\test_afip_process_isolated_router.py `
  tests\test_afip_sequential_profile_router.py `
  tests\test_afip_sequential_router_startup.py `
  tests\test_afip_v1_production_finalization_big_pack.py `
  tests\test_milestone_s_pack_4.py
exit $LASTEXITCODE
