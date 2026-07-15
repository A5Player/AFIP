$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pytest tests\test_milestone_s_pack_5_1.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools\afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "AFIP Milestone S Pack 5.1 validation: PASS"
