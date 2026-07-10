pytest tests/test_milestone_i_pack_7_etf_flow_intelligence.py -v
if ($LASTEXITCODE -ne 0) { exit }
pytest
if ($LASTEXITCODE -ne 0) { exit }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit }
git add .
git commit -m "Milestone I Pack 7 ETF Flow Intelligence"
git push
