@echo off
pytest tests/test_milestone_k_pack_1_execution_intelligence_foundation.py -v || exit /b 1
pytest || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
git add . || exit /b 1
git commit -m "Milestone K Pack 1 Execution Intelligence Foundation" || exit /b 1
git push || exit /b 1
