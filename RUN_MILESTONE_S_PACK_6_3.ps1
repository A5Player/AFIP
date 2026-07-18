$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone S Pack 6.3 ==="
python -m pytest tests/test_milestone_s_pack_6_3.py -v
python tools/validate_financial_naming.py
python afip.py simulate
python afip.py mt5-check
python -m pytest -q
Write-Host "Pack 6.3 validation complete. Execution authority remains NONE."
