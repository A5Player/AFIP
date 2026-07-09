pytest tests/test_production_milestone_h_pack_3.py -v
if ($LASTEXITCODE -ne 0) { exit }

pytest
if ($LASTEXITCODE -ne 0) { exit }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }

git add .
git commit -m "Production Milestone H Pack 3 Profile Manager Setup Wizard Connection Manager Historical Data Manager Dashboard Runtime"
git push
