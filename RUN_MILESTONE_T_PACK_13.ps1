$ErrorActionPreference = "Continue"
Write-Host "=== AFIP Milestone T Pack 13 ==="
Write-Host "Position Care and Exit Supervision"
python -m pytest tests/test_milestone_t_pack_13_position_care_runtime.py -q
python tools/afip_local_quality_check.py
Write-Host "Milestone T Pack 13 validation completed."
