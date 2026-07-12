# Validation Guide — Milestone S Pack 2

1. Extract the patch into the AFIP repository root and allow matching files to merge.
2. Run `SET_AFIP_PROFILE_CREDENTIALS_LOCAL.ps1` once on the VPS. Close and reopen PowerShell.
3. Confirm each MT5 installation contains `terminal64.exe` in its configured folder.
4. From the AFIP repository root, activate `.venv` and run:

```powershell
python tools/afip_four_profile_control.py status
pytest tests/test_milestone_s_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
python afip.py mt5-check
```

5. Prepare P1 and P4:

```powershell
python tools/afip_four_profile_control.py prepare --profiles P1 P4
```

6. With MT5 terminals already open, start isolated locked-simulation workers:

```powershell
python tools/afip_four_profile_control.py start-selected --profiles P1 P4
```

7. Check status:

```powershell
python tools/afip_four_profile_control.py status
```

8. Stop safely:

```powershell
python tools/afip_four_profile_control.py stop-selected --profiles P1 P4
```

Expected safety fields for every profile: `LOCKED_SIMULATION_ONLY`, `NO_ORDER_SENT`, `direct_execution=false`, `live_execution=false`.
