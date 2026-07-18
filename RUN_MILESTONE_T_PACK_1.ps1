$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone T Pack 1 ==="
Write-Host "Research Quarantine & Knowledge Promotion Foundation"

python -m pytest tests/test_milestone_t_pack_1_research_quarantine.py -q
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py

Write-Host "Milestone T Pack 1 validation completed."
