pytest tests/test_milestone_j_pack_5_trade_scoring.py -v
if ($LASTEXITCODE -ne 0) { exit }
pytest
if ($LASTEXITCODE -ne 0) { exit }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit }
git add .
git commit -m "Milestone J Pack 5 Trade Scoring Engine"
git push
