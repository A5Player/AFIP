$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pytest tests/test_phase_u_pack_3_3_8_position_sizing_authority.py tests/test_milestone_s_pack_4.py tests/test_milestone_s_pack_4_6.py tests/test_milestone_s_pack_4_7.py tests/test_production_milestone_h_pack_5.py tests/test_production_milestone_h_pack_9.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q
exit $LASTEXITCODE
