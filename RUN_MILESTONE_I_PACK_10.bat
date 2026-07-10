@echo off
pytest tests/test_milestone_i_pack_10_market_regime_v2.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add . || exit /b 1
git commit -m "Milestone I Pack 10 Market Regime V2" || exit /b 1
git push
