@echo off
pytest tests/test_milestone_i_pack_7_etf_flow_intelligence.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add .
git commit -m "Milestone I Pack 7 ETF Flow Intelligence"
git push
