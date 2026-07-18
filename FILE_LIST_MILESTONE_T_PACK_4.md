# AFIP Milestone T Pack 4 — File List

## Added

- `afip/exit_outcome_research/__init__.py`
- `afip/exit_outcome_research/runtime.py`
- `tests/test_milestone_t_pack_4_exit_outcome_research.py`
- `README_MILESTONE_T_PACK_4.md`
- `README_MILESTONE_T_PACK_4_TH.md`
- `FILE_LIST_MILESTONE_T_PACK_4.md`
- `RUN_MILESTONE_T_PACK_4.ps1`
- `RUN_MILESTONE_T_PACK_4.bat`
- `APPLY_MILESTONE_T_PACK_4_DOC_UPDATES.ps1`
- `AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_4_APPEND.md`
- `HANDOFF_MILESTONE_T_PACK_4_APPEND.md`
- `VALIDATION_MILESTONE_T_PACK_4.txt`

## Modified

- `afip/historical_replay_research/runtime.py`
  - expands the append-only research dataset registry with Pack 4 datasets
  - does not change historical replay behavior or Production Runtime

## Production Boundary

- Production Runtime: unchanged
- Production Trading Logic: unchanged
- MT5 execution: none
- Research state: `EXPERIMENTAL`
- Production usable: false
