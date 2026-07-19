$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m pytest tests/test_phase_u_pack_3_4_9.py tests/test_phase_u_pack_3_4_10.py tests/test_phase_u_final_research.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'AFIP Phase U Final validation PASS.'
