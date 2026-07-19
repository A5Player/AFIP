$ErrorActionPreference = "Continue"
Write-Host "=== AFIP Milestone T Pack 15 ==="
Write-Host "Production Certification, Safety Evidence and Regression Closure"
python -m pytest tests/test_milestone_t_pack_15_production_certification.py -q
python tools/afip_local_quality_check.py
Write-Host "Milestone T Pack 15 validation completed."
