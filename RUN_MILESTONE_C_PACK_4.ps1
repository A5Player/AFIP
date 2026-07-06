# AFIP Production Milestone C Pack 4
# Single-run validation and Git publishing command set.

pytest tests/test_production_milestone_c_pack_4.py -v

if ($LASTEXITCODE -ne 0) { exit }

pytest

if ($LASTEXITCODE -ne 0) { exit }

python tools/afip_local_quality_check.py

if ($LASTEXITCODE -ne 0) { exit }

git add .

git commit -m "Production Milestone C Pack 4"

git push
