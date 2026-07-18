@echo off
python -m pytest tests\test_milestone_s_pack_4_9_emergency_execution_safety.py -v
if errorlevel 1 exit /b 1
python tools\afip_pack_4_9_source_audit.py
