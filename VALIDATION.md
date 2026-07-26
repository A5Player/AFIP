# Runtime Repair Validation

Run in Windows PowerShell.

## 1. Confirm repository and syntax

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1

git log -1 --oneline
git status --short
git diff --stat

python -m py_compile `
  tools\afip_profile_execution_once.py `
  afip\demo_execution_gateway\runtime.py `
  afip\four_profile_operations\runtime.py

python -m pytest -q `
  tests\test_afip_v1_runtime_execution_repair_pack_1.py `
  tests\test_afip_process_isolated_router.py `
  tests\test_afip_sequential_profile_router.py `
  tests\test_afip_v1_runtime_certification_repair_pack_2.py `
  tests\test_afip_v1_runtime_truth_passive_monitoring_final.py
```

Expected focused result: all tests pass.

## 2. Confirm exactly four manually opened terminals before start

```powershell
Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" |
  Select-Object ProcessId, ExecutablePath |
  Sort-Object ExecutablePath |
  Format-Table -AutoSize
```

Expected executable paths, one process each:

- `C:\XM Global MT5 P1\terminal64.exe`
- `C:\XM Global MT5 P2\terminal64.exe`
- `C:\XM Global MT5 P3\terminal64.exe`
- `C:\XM Global MT5 P4\terminal64.exe`

Each terminal must already be logged in and connected. Do not let AFIP open MT5.

## 3. Start AFIP

```powershell
cd C:\AFIP
.\START_AFIP.ps1
```

## 4. Confirm process count did not increase

```powershell
Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" |
  Select-Object ProcessId, ExecutablePath |
  Sort-Object ExecutablePath |
  Format-Table -AutoSize
```

Expected: still exactly four terminal processes. No login/password dialog.

## 5. Inspect Runtime Authority

```powershell
python -m tools.afip_demo_execution_control status
Get-Content .\runtime\execution\sequential_router_status.json -Raw
Get-Content .\runtime\final_integration_status.json -Raw
```

Expected after startup handshake/cycle:

- Router `running = true`
- Router state `BOOTING` then `RUNNING`
- P1-P4 `runtime_state = RUNNING`
- No `mt5_terminal_not_running_manual_start_required`
- No `duplicate_mt5_terminal_process`
- No `mt5_initialize_failed (-10003)`

## 6. Dashboard and research

```powershell
Get-Content .\runtime\dashboard\dashboard_monitor_status.json -Raw
Get-Content .\runtime\research\research_engine_status.json -Raw
```

Expected:

- Dashboard monitor remains running.
- Dashboard reads Runtime Authority and reaches Runtime `4/4` after all four profile workers bind successfully.
- Research Runtime remains operational.

## Safe failure behavior

If any configured MT5 terminal is not already running, AFIP must block that profile with:

`mt5_terminal_not_running_manual_start_required`

It must not start a terminal or display a login dialog.
