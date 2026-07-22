param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
if (Test-Path ".\.venv\Scripts\Activate.ps1") { . ".\.venv\Scripts\Activate.ps1" }
python -m pytest -q `
  tests/test_afip_v1_production_finalization_big_pack.py `
  tests/test_afip_final_execution_ownership.py `
  tests/test_afip_process_isolated_router.py `
  tests/test_afip_final_capital_tier_authority.py `
  tests/test_milestone_s_pack_5_5.py `
  tests/test_milestone_s_pack_7_1_position_ceiling_semantics.py `
  tests/test_milestone_s_pack_7_2_position_capacity_policy.py `
  tests/test_phase_u_pack_3_3_7_final_certification.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -c "from afip.production_runtime_authority import clean_stale_runtime,build_dashboard_snapshot; clean_stale_runtime('.'); build_dashboard_snapshot([],'.'); print('AFIP production runtime authority: READY')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
exit $LASTEXITCODE
