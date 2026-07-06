@echo off
setlocal
cd /d %~dp0
echo === AFIP Production Milestone C Pack 13 ===
python -m pytest tests/test_production_milestone_c_pack_13.py -v || exit /b 1
python -m pytest -q || exit /b 1
python tools/afip_local_quality_check.py || exit /b 1
echo === Pack 13 complete ===
