pytest tests/test_milestone_k_pack_2_smart_entry.py -v
if ($LASTEXITCODE -ne 0) { exit }
pytest
if ($LASTEXITCODE -ne 0) { exit }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit }
git add .
git commit -m "Milestone K Pack 2 Smart Entry Engine"
if ($LASTEXITCODE -ne 0) { exit }
git push
