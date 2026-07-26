# AFIP V1 Runtime Truth Recovery Final

## Scope
Patch-only repair against the supplied AFIP(63).zip repository. This pack does not change trading logic, lot sizing, SL/TP, signal thresholds, safety gates, execution authority, or live-trading state.

## Root cause repaired
1. Passive MT5 process observation had two incompatible process-detection contracts. Legacy callers/tests expected `_terminal_process_alive`, while the current manager only exposed a bulk path snapshot.
2. Dashboard operations health was calculated before the authoritative runtime-truth model was attached, so it could retain conflicting runtime/MT5/financial interpretations.
3. Passive broker-session semantics and financial snapshot semantics were not exposed consistently to all dashboard consumers.
4. A legacy dashboard contract string had to remain available without restoring the obsolete `Fresh data` label in current passive-truth output.

## Source files changed
- `afip/four_profile_operations/mt5_connection.py`
- `afip/runtime_truth.py`
- `afip/dashboard_data_contract.py`
- `afip/dashboard_operations_health.py`
- `afip/dashboard_ui/split_runtime.py`
- `tests/test_afip_v1_runtime_truth_recovery_final.py`

## Safety behavior
- Passive CLI remains passive because `tools/afip_mt5_multi_terminal_check.py` explicitly passes `active=args.active`; without `--active`, this is `False`.
- Dashboard contract and live services explicitly call `active=False`.
- Passive mode never constructs the MT5 adapter, initializes MT5, logs in, reconnects, launches a terminal, or sends an order.
- Active diagnostic remains explicit through `--active`.

## Verified results in supplied source
- Focused Runtime Truth/Dashboard regression: `49 passed`
- Full regression: `2753 passed`
- Changed-file Python compilation: PASS

## Existing unrelated source issue discovered
`python -m compileall afip tools` is blocked by pre-existing syntax errors in:
- `tools/afip_financial_architecture_freeze.py`
- `tools/afip_naming_migration.py`

Those files are outside Runtime Truth scope and are not modified by this pack. The installer compiles every modified source file and runs focused regression. The validator additionally supports full regression.

## Install
```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1

# Extract this ZIP to any temporary folder, then run:
.\INSTALL_AFIP_V1_RUNTIME_TRUTH_RECOVERY_FINAL.ps1 -ProjectRoot C:\AFIP
```

## Validate
```powershell
cd C:\AFIP
.\.venv\Scripts\Activate.ps1
.\VALIDATE_AFIP_V1_RUNTIME_TRUTH_RECOVERY_FINAL.ps1 -ProjectRoot C:\AFIP -FullRegression
```

The validator never runs the active MT5 diagnostic automatically.
