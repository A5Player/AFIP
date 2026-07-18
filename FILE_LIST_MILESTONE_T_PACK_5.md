# AFIP Milestone T Pack 5 — File List

## Added

- `afip/exit_evidence_research/__init__.py`
- `afip/exit_evidence_research/runtime.py`
- `tests/test_milestone_t_pack_5_exit_evidence_research.py`
- `README_MILESTONE_T_PACK_5.md`
- `README_MILESTONE_T_PACK_5_TH.md`
- `FILE_LIST_MILESTONE_T_PACK_5.md`
- `RUN_MILESTONE_T_PACK_5.ps1`
- `RUN_MILESTONE_T_PACK_5.bat`
- `APPLY_MILESTONE_T_PACK_5_DOC_UPDATES.ps1`
- `AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_5_APPEND.md`
- `HANDOFF_MILESTONE_T_PACK_5_APPEND.md`
- `VALIDATION_MILESTONE_T_PACK_5.txt`

## Modified

- `afip/historical_replay_research/runtime.py`
  - registers Pack 5 append-only research datasets
  - does not change replay or Production behavior

## Production Boundary

- Production Runtime: unchanged
- Production Trading Logic: unchanged
- MT5 execution: none
- Research state: `EXPERIMENTAL`
- Production usable: false
