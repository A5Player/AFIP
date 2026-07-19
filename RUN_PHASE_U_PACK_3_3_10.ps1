$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Phase U Pack 3.3.10 ==="
Write-Host "Production Contract Alignment"

python -m pytest -q tests/test_phase_u_pack_3_3_1_timeframe_registry.py tests/test_phase_u_pack_3_3_6_profile_execution_research_control.py tests/test_phase_u_pack_3_3_7_final_certification.py tests/test_phase_u_pack_3_3_9_historical_readiness_compatibility.py
if ($LASTEXITCODE -ne 0) { throw "Pack regression failed." }

Write-Host "Running full regression..."
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Full regression failed." }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { throw "Local quality check failed." }

python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw "Dashboard generation failed." }

Write-Host "Phase U Pack 3.3.10 PASS"
