$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (Test-Path ".\.venv\Scripts\Activate.ps1") { . ".\.venv\Scripts\Activate.ps1" }
Write-Host "AFIP V1 Final Runtime Observatory validation" -ForegroundColor Cyan
python -m pytest tests/test_afip_v1_final_runtime_observatory.py tests/test_phase_v_major_pack.py tests/test_phase_u_pack_3_6_dashboard_authority.py tests/test_phase_u_pack_3_6_revision_1_compact_operations_header.py -q
python -m afip.dashboard_ui
python tools/afip_local_quality_check.py
python -m pytest -q
Write-Host "Validation complete. Review git status before commit." -ForegroundColor Green
git status
git diff --name-only
git diff --cached --name-only
