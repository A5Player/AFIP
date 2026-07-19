$ErrorActionPreference='Stop'; Set-Location $PSScriptRoot
python -m pytest tests/test_phase_u_pack_3_4_10.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_phase_u_pack_3_4_10_collector.py --root . --once
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'Phase U Pack 3.4.10 one research cycle completed.'
