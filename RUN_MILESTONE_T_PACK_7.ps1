$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 7 ==="
Write-Host "Research-Derived Initial Standard, Context Selection & Historical Coverage Foundation"
python -m pytest -q tests/test_milestone_t_pack_7_research_standardization.py
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py
Write-Host "Milestone T Pack 7 validation completed."
