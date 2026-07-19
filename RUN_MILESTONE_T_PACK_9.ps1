$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 9 ==="
Write-Host "MT5 Historical Provider, Resumable Backfill, Decision Trace Wiring & Dashboard Data Contract Foundation"
python -m pytest -q tests/test_milestone_t_pack_9_mt5_historical_integration.py
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py
Write-Host "Milestone T Pack 9 validation completed."
