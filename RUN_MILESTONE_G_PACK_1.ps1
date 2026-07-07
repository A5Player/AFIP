pytest tests/test_production_milestone_g_pack_1.py -v
if ($LASTEXITCODE -ne 0) { exit }
pytest
if ($LASTEXITCODE -ne 0) { exit }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }
