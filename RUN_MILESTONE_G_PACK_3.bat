pytest tests/test_production_milestone_g_pack_3.py -v
IF ERRORLEVEL 1 EXIT /B 1

pytest
IF ERRORLEVEL 1 EXIT /B 1

python tools/afip_local_quality_check.py
IF ERRORLEVEL 1 EXIT /B 1
