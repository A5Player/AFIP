$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.3.7 - Final Integration, Regression & Certification"
Write-Host "Safety: stop active AFIP execution and research writers before certification."
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
try { & (Join-Path $Root 'APPLY_PHASE_U_PACK_3_3_7_DOC_UPDATES.ps1') }
catch { throw "Documentation update failed: $($_.Exception.Message)" }

python -m pytest -q `
  tests/test_phase_u_pack_3_3_1_timeframe_registry.py `
  tests/test_phase_u_pack_3_3_2_m30_historical_data_lake.py `
  tests/test_phase_u_pack_3_3_3_m30_replay_coverage.py `
  tests/test_phase_u_pack_3_3_4_m30_quality_backfill.py `
  tests/test_phase_u_pack_3_3_5_dashboard_timeframe_status.py `
  tests/test_phase_u_pack_3_3_6_profile_execution_research_control.py `
  tests/test_phase_u_pack_3_3_7_final_certification.py
if ($LASTEXITCODE -ne 0) { throw "Phase U Pack 3.3.7 certification failed." }

Write-Host "PASS - Phase U Pack 3.3 final integration and regression certification validated."
Write-Host "P1/P4 execution enabled; P2/P3 execution disabled with configuration, data, and research preserved."
Write-Host "Live execution policy was not changed. Real-account readiness was not certified."
