pytest tests/test_production_milestone_e_pack_8.py -v

if ($LASTEXITCODE -ne 0) { exit }

pytest

if ($LASTEXITCODE -ne 0) { exit }

python tools/afip_local_quality_check.py

if ($LASTEXITCODE -ne 0) { exit }

git add .

git commit -m "Production Milestone E Pack 8"

git push
