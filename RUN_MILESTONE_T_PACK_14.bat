@echo off
echo === AFIP Milestone T Pack 14 ===
echo Unattended Continuity, Restart Reconciliation and Recovery Supervision
python -m pytest tests/test_milestone_t_pack_14_unattended_continuity.py -q
python tools/afip_local_quality_check.py
echo Milestone T Pack 14 validation completed.
