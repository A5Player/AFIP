# Validation Guide — Milestone S Pack 5.2

Run from the repository root after activating `.venv`.

```powershell
pytest tests/test_milestone_s_pack_5_1.py tests/test_milestone_s_pack_5_2.py
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Expected pack-specific result: all tests pass.

Confirm:
1. Trade cases include M15/M30/H1/H4/D1.
2. A checkpoint cannot be recorded before its scheduled time.
3. Replay rejects candles beyond visible history.
4. Replay statistics show `optimization_enabled: false`.
5. Dashboard contains `research_foundation` as a permanent bottom section.
6. Similar-pattern monitor shows `affects_trading: false`.

## Git
```powershell
git status
git add AFIP_PROJECT_DATABASE.md HANDOFF.md FILE_LIST_MILESTONE_S_PACK_5_2.md README_MILESTONE_S_PACK_5_2.md README_MILESTONE_S_PACK_5_2_TH.md VALIDATION_GUIDE_MILESTONE_S_PACK_5_2.md RUN_MILESTONE_S_PACK_5_2.ps1 RUN_MILESTONE_S_PACK_5_2.bat afip/research_data_foundation afip/dashboard_ui/runtime.py tests/test_milestone_s_pack_5_1.py tests/test_milestone_s_pack_5_2.py
git commit -m "Milestone S Pack 5.2 trade case and historical research foundation"
git push origin main
```

## Rollback
```powershell
git revert HEAD
git push origin main
```

For an uncommitted patch only:
```powershell
git restore AFIP_PROJECT_DATABASE.md HANDOFF.md afip/research_data_foundation afip/dashboard_ui/runtime.py tests/test_milestone_s_pack_5_1.py
git clean -f FILE_LIST_MILESTONE_S_PACK_5_2.md README_MILESTONE_S_PACK_5_2.md README_MILESTONE_S_PACK_5_2_TH.md VALIDATION_GUIDE_MILESTONE_S_PACK_5_2.md RUN_MILESTONE_S_PACK_5_2.ps1 RUN_MILESTONE_S_PACK_5_2.bat tests/test_milestone_s_pack_5_2.py
```
