@echo off
pytest tests/test_milestone_j_pack_10_decision_intelligence_certification.py -v
if errorlevel 1 exit /b %errorlevel%
pytest
if errorlevel 1 exit /b %errorlevel%
python tools/afip_local_quality_check.py
if errorlevel 1 exit /b %errorlevel%
python -m afip.dashboard_ui
if errorlevel 1 exit /b %errorlevel%
git add .
git commit -m "Milestone J Pack 10 Decision Intelligence Certification"
if errorlevel 1 exit /b %errorlevel%
git push
