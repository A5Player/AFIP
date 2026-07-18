$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone S Pack 5.4.1 Validation ==="
python -m pytest tests/test_milestone_s_pack_5_4_1.py tests/test_milestone_s_pack_5_4.py -q
python tools/validate_financial_naming.py
python tools/afip_mt5_multi_terminal_check.py --profiles P1 P2 P3 P4 --reconnect-attempts 2
Write-Host "Pack 5.4.1 validation completed."
