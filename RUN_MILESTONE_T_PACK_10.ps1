$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 10 ==="
Write-Host "Adaptive Multi-Objective Plan Ranking and Capital Preservation"
python -m pytest -q tests/test_milestone_t_pack_10_adaptive_plan_ranking.py
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py
python -m pytest -q
Write-Host "Milestone T Pack 10 validation completed."
