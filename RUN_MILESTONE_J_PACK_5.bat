@echo off
pytest tests/test_milestone_j_pack_5_trade_scoring.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add .
git commit -m "Milestone J Pack 5 Trade Scoring Engine"
git push
