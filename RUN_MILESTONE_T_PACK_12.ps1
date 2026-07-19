$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 12 ==="
Write-Host "Certified Trade Plan Runtime Orchestration"
python -m pytest -q tests/test_milestone_t_pack_12_trade_plan_runtime.py
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py
Write-Host "Milestone T Pack 12 validation completed."
