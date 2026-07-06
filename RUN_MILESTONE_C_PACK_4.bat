@echo off
REM AFIP Production Milestone C Pack 4
REM Single-run validation and Git publishing command set.

pytest tests/test_production_milestone_c_pack_4.py -v
if errorlevel 1 exit /b 1

pytest
if errorlevel 1 exit /b 1

python tools/afip_local_quality_check.py
if errorlevel 1 exit /b 1

git add .

git commit -m "Production Milestone C Pack 4"
if errorlevel 1 exit /b 1

git push
