pytest tests/test_production_milestone_c_pack_1.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

git add .
git commit -m "Production Milestone C Pack 1"
git push
