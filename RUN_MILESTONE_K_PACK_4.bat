@echo off
pytest tests/test_milestone_k_pack_4_dynamic_stop_loss.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add . || exit /b 1
git commit -m "Milestone K Pack 4 Dynamic Stop Loss Intelligence" || exit /b 1
git push || exit /b 1
