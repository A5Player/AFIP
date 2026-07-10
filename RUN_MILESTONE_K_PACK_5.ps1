pytest tests/test_milestone_k_pack_5_dynamic_take_profit.py -v
if ($LASTEXITCODE -ne 0) { exit }
pytest
if ($LASTEXITCODE -ne 0) { exit }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit }
git add .
git commit -m "Milestone K Pack 5 Dynamic Take Profit Intelligence"
if ($LASTEXITCODE -ne 0) { exit }
git push
