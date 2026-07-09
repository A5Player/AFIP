pytest tests/test_production_milestone_h_pack_7.py -v
if ($LASTEXITCODE -ne 0) { exit }
pytest
if ($LASTEXITCODE -ne 0) { exit }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }
git add .
git commit -m "Production Milestone H Pack 7 Paper Trading Engine"
git push
