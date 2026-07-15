@echo off
pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_7.py || exit /b 1
pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
