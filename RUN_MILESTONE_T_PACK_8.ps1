$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 8 ==="
Write-Host "Runtime Standard Adapter and Historical Backfill Orchestration"
python -m pytest -q tests/test_milestone_t_pack_8_runtime_standard_adapter.py
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py
python -m pytest -q
Write-Host "Milestone T Pack 8 validation completed."
