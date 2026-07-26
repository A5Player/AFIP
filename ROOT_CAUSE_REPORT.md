# AFIP V1 Final — Production Runtime Root Cause Report

## Repository audited

- Uploaded source: `AFIP(65).zip`
- Audited repository root: `AFIP/`
- Git HEAD: `0e8b004 AFIP V1 Final Production Certification`
- The uploaded working tree contains many pre-existing modifications. This repair package changes only the four files listed below.

## Confirmed startup execution flow

1. `START_AFIP.ps1:4` executes `python -m tools.afip_final_integration start`.
2. `tools/afip_final_integration.py:29-30` calls `FinalIntegrationRuntime.start()`.
3. `afip/final_integration/runtime.py:36` calls `tools.afip_demo_execution_control start-all`.
4. `tools/afip_demo_execution_control.py:197` performs account-isolation verification, then lines `220-237` start the single sequential router process.
5. `tools/afip_profile_sequential_execution_router.py:74-96` starts one short-lived `tools.afip_profile_execution_once` worker for each enabled profile.
6. In the original uploaded source, `tools/afip_profile_execution_once.py:22-45` defined `_ensure_target_terminal()`, and lines `36-41` called:

   `subprocess.Popen([str(terminal), "/portable"], ...)`

7. The original `run_once()` called `_ensure_target_terminal(profile)` immediately before `DemoExecutionGateway.run_cycle()`.
8. Therefore every P1-P4 worker explicitly started another configured MT5 executable before the gateway called `MetaTrader5.initialize(...)`.

## Root cause

### Primary defect

**File:** `tools/afip_profile_execution_once.py`  
**Function:** `_ensure_target_terminal()`  
**Original behavior:** unconditionally launched the configured `terminal64.exe /portable` for every enabled profile on every router cycle.

This is the exact source of the observed four additional MT5 windows. With four manually opened terminals, the first router cycle created another P1, P2, P3, and P4, producing eight processes total. Login dialogs appeared because the new portable instances did not share the already-authenticated UI session state in the expected way.

### Secondary defect

**File:** `afip/four_profile_operations/runtime.py`  
**Function:** `FourProfileOperationalRuntime.launch_mt5()`  
**Original behavior:** contained a second explicit `subprocess.Popen([terminal64.exe, "/portable"])` launch path. It was not the direct `START_AFIP.ps1` path in the observed incident, but it violated the same production policy and remained callable through the four-profile control utility.

### Consequential runtime state

The router stayed `NOT_STARTED` because account-isolation verification and/or profile worker initialization failed after the duplicate terminal processes appeared. `Dashboard Runtime 0/4` was a correct downstream representation of Runtime Authority, not a dashboard defect.

## Repair applied

### 1. Worker is attach-only and fail-closed

`tools/afip_profile_execution_once.py`

- Removed all `subprocess.Popen` and `/portable` terminal-launch logic.
- Replaced `_ensure_target_terminal()` with `_require_target_terminal_running()`.
- The worker now uses read-only CIM process evidence and requires exactly one process matching the configured executable path.
- Zero matches: `mt5_terminal_not_running_manual_start_required`.
- More than one match: `duplicate_mt5_terminal_process`.
- Only after this check does the existing gateway attempt to bind to the already-running configured terminal.

### 2. Gateway rechecks process truth before initialization

`afip/demo_execution_gateway/runtime.py`

- Added `_manual_terminal_running()` using the existing passive MT5 process observer.
- Added fail-closed checks before normal preflight initialization and before exact-binding repair initialization.
- No changes were made to lot sizing, capital authority, TP, SL, confidence, risk, routing sequence, order logic, research logic, or strategy.

### 3. Legacy launch command disabled

`afip/four_profile_operations/runtime.py`

- `launch_mt5()` no longer starts `terminal64.exe`.
- It returns a blocked/manual-start-required result when a profile requests automatic launch.
- Existing folder structure and supervisor architecture remain unchanged.

### 4. Obsolete regression expectation corrected

`tests/test_afip_v1_runtime_execution_repair_pack_1.py`

- Removed the old assertion that required AFIP to prelaunch MT5.
- Added assertions requiring manual-terminal checks and forbidding `subprocess.Popen` in the profile worker.

## Source audit results

- No explicit `terminal64.exe /portable` launch remains in `afip/` or `tools/`.
- The remaining `subprocess.Popen` calls start AFIP Python processes only: router, profile worker, dashboard, research, and runtime workers.
- `MetaTrader5.initialize(path=...)` remains in the isolation verifier and demo gateway because it is the existing bridge-binding mechanism. It is now preceded by exact read-only process existence/uniqueness checks in the production execution path.
- No runtime JSON state files were patched. Runtime Authority will be rewritten naturally by the existing runtime after a successful start.

## Validation completed in the audit environment

- Python compilation passed for all three modified production source files.
- Focused runtime regression suite: `17 passed in 0.30s`.
- Static scan confirmed no explicit MT5 terminal launch expression remains.

## Host validation still required

The Linux audit environment cannot prove Windows MT5 IPC attachment or produce a real `Router = RUNNING / Dashboard = 4/4` result. Those outcomes require the user's Windows host with the four manually opened XM terminals and configured credentials. The included validation procedure checks these production conditions without changing trading policy.
