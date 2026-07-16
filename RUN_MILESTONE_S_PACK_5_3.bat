@echo off
python -m pytest tests\test_milestone_s_pack_5_3.py -v || exit /b 1
python -m tools.afip_research_runtime_collector || exit /b 1
python -m pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
