@echo off
setlocal
python -m pytest -q tests\test_milestone_t_pack_5_exit_evidence_research.py
if errorlevel 1 exit /b %errorlevel%
python tools\validate_financial_naming.py
if errorlevel 1 exit /b %errorlevel%
python tools\afip_local_quality_check.py
if errorlevel 1 exit /b %errorlevel%
echo Milestone T Pack 5 validation completed.
