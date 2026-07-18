@echo off
setlocal

echo === AFIP Milestone T Pack 1 ===
echo Research Quarantine ^& Knowledge Promotion Foundation

python -m pytest tests/test_milestone_t_pack_1_research_quarantine.py -q
if errorlevel 1 exit /b 1
python tools/validate_financial_naming.py
if errorlevel 1 exit /b 1
python tools/afip_local_quality_check.py
if errorlevel 1 exit /b 1

echo Milestone T Pack 1 validation completed.
endlocal
