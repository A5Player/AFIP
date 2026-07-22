param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
& $python -m pytest -q `
  tests/test_afip_account_isolation_capital_safety.py `
  tests/test_afip_final_account_routing_realtime_ranking_fix.py `
  tests/test_afip_v1_certification_performance_hotfix.py `
  tests/test_phase_u_pack_3_5_lot_authority.py `
  tests/test_production_bringup_pack_10.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Targeted certification repair tests PASS."
Write-Host "Run full regression with: $python -m pytest -q"
