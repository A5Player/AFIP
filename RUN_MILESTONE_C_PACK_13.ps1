$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Production Milestone C Pack 13 ==="
python -m pytest tests/test_production_milestone_c_pack_13.py -v
python -m pytest -q
python tools/afip_local_quality_check.py
Write-Host "=== Pack 13 complete ==="
