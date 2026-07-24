$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python tools/afip_v1_pack_5_repository_cleanup.py
python -m pytest -q tests/test_afip_v1_pack_5_final_cleanup_certification.py tests/test_afip_v1_pack_4_production_certification_repair.py tests/test_afip_v1_runtime_certification_repair_pack_2.py tests/test_afip_final_execution_ownership.py tests/test_afip_process_isolated_router.py tests/test_phase25_position_protection.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_v1_pack_4_demo_execution_certification.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_v1_pack_5_final_runtime_certification.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "AFIP V1 Final Pack 5: ALL TESTS PASS"
