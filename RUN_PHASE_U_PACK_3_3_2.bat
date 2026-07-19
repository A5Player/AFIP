@echo off
cd /d %~dp0
python -m pytest tests/test_phase_u_pack_3_3_1_timeframe_registry.py tests/test_phase_u_pack_3_3_2_m30_historical_data_lake.py -q
if errorlevel 1 exit /b 1
echo PASS - M30 historical collection and append-only data lake integration validated.
