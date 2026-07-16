# Validation Guide — Milestone S Pack 5.4

## Pack-specific test

```powershell
python -m pytest tests\test_milestone_s_pack_5_4.py -v
```

## Full regression and quality

```powershell
python -m pytest
python tools\afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git

```powershell
git add AFIP_PROJECT_DATABASE.md HANDOFF.md afip\research_data_foundation\__init__.py afip\research_data_foundation\aggregator.py afip\research_data_foundation\dashboard.py afip\dashboard_ui\runtime.py tests\test_milestone_s_pack_5_4.py FILE_LIST_MILESTONE_S_PACK_5_4.md README_MILESTONE_S_PACK_5_4.md README_MILESTONE_S_PACK_5_4_TH.md VALIDATION_GUIDE_MILESTONE_S_PACK_5_4.md RUN_MILESTONE_S_PACK_5_4.ps1 RUN_MILESTONE_S_PACK_5_4.bat
git diff --cached --stat
git commit -m "Milestone S Pack 5.4 - Research Aggregator and Live Dashboard Projection"
git push origin main
```

## Rollback

Before push: `git reset --hard HEAD~1`

After push: `git revert HEAD` followed by `git push origin main`
