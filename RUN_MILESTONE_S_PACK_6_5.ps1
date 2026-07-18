$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "=== AFIP Milestone S Pack 6.5 ==="
python -m pytest tests/test_milestone_s_pack_6_5.py -v
python tools/validate_financial_naming.py
python afip.py simulate
python afip.py mt5-check
python -m pytest -q
Write-Host "Pack 6.5 validation complete. Execution authority remains NONE."
