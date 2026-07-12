# AFIP Version 1.0 — Milestone S Pack 2
## Four-Profile Demo Operational Configuration

Pack 2 adds isolated operations for four XM / GOLD# profiles while preserving `LOCKED_SIMULATION_ONLY`, `direct_execution=False`, `live_execution=False`, and `NO_ORDER_SENT`.

### Default profile mapping

| Profile | Policy | MT5 folder | Server | Default |
|---|---|---|---|---|
| P1 | High Safety | `C:\XM Global MT5 P1` | `XMGlobal-MT5 6` | ON |
| P2 | Balanced | `C:\XM Global MT5 P2` | `XMGlobal-MT5 6` | OFF |
| P3 | High Risk Within Plan | `C:\XM Global MT5 P3` | `XMGlobal-MT5 5` | OFF |
| P4 | Research | `C:\XM Global MT5 P4` | `XMGlobal-MT5 5` | ON |

Account logins and passwords are deliberately excluded from tracked files. Run `SET_AFIP_PROFILE_CREDENTIALS_LOCAL.ps1` on the VPS. It saves credentials in Windows user environment variables. Never commit credentials.

### Control commands

```powershell
python tools/afip_four_profile_control.py status
python tools/afip_four_profile_control.py prepare --profiles P1 P4
python tools/afip_four_profile_control.py launch-mt5 --profiles P1 P4
python tools/afip_four_profile_control.py start-selected --profiles P1 P4
python tools/afip_four_profile_control.py restart-selected --profiles P1 P4
python tools/afip_four_profile_control.py stop-selected --profiles P1 P4
python tools/afip_four_profile_control.py start-all
python tools/afip_four_profile_control.py stop-all
```

`launch_mt5` obeys each profile's `launch_mt5` flag. The default is `false`, so AFIP connects to terminals already opened by the operator. Change only the boolean in `config/four_profile_demo.json` when automatic terminal launch is required.

### Isolation

Each profile has separate Runtime, Database, Logs, Dashboard, Learning, Knowledge, and Statistics paths under `runtime/profiles/p1` through `p4`. Duplicate MT5 folders, terminals, configured accounts, runtime paths, databases, and supporting paths are blocked before startup.

### Validation

```powershell
pytest tests/test_milestone_s_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
python afip.py mt5-check
```
