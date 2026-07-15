$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

& python -m pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_7.py tests\test_milestone_s_pack_4_8.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& python tools\validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
