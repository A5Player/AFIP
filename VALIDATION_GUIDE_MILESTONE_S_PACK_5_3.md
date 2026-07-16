# Validation Guide — Milestone S Pack 5.3

## Pack Test
```powershell
python -m pytest tests\test_milestone_s_pack_5_3.py -v
```

## Runtime Ledger Collection
```powershell
python -m tools.afip_research_runtime_collector
```

## Full Regression
```powershell
python -m pytest
```

## Local Quality Check
```powershell
python tools\afip_local_quality_check.py
```

## Dashboard Rebuild
```powershell
python -m afip.dashboard_ui
```

## Git
```powershell
git add AFIP_PROJECT_DATABASE.md HANDOFF.md afip\research_data_foundation\__init__.py afip\research_data_foundation\runtime_collector.py tools\afip_research_runtime_collector.py tests\test_milestone_s_pack_5_3.py FILE_LIST_MILESTONE_S_PACK_5_3.md README_MILESTONE_S_PACK_5_3.md README_MILESTONE_S_PACK_5_3_TH.md VALIDATION_GUIDE_MILESTONE_S_PACK_5_3.md RUN_MILESTONE_S_PACK_5_3.ps1 RUN_MILESTONE_S_PACK_5_3.bat
git commit -m "Milestone S Pack 5.3 - Runtime Research Data Wiring"
git push origin main
```

## Rollback
```powershell
git revert HEAD
git push origin main
```
