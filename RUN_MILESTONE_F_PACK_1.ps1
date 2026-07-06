$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Production Milestone F Pack 1 ==="
python -m pytest tests/test_production_milestone_f_pack_1.py -v
python -m pytest
python tools/afip_local_quality_check.py
Write-Host "=== Milestone F Pack 1 PASS ==="
