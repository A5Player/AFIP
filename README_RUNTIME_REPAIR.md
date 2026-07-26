# AFIP Runtime Repair

This package is a direct source overlay for the repository at `C:\AFIP`.

## Patched files

- `tools\afip_profile_execution_once.py`
- `afip\demo_execution_gateway\runtime.py`
- `afip\four_profile_operations\runtime.py`
- `tests\test_afip_v1_runtime_execution_repair_pack_1.py`

No installer and no self-modifying script are included.

## Apply

1. Stop AFIP using the existing `STOP_AFIP.ps1`.
2. Close only duplicate/unwanted MT5 windows. Leave exactly one manually opened and logged-in terminal for each P1-P4 path.
3. Back up the four destination files.
4. Copy the contents of this folder over `C:\AFIP`, preserving folders and allowing file replacement.
5. Run the commands in `VALIDATION.md`.

PowerShell overlay example from the extracted package parent directory:

```powershell
Copy-Item -Path .\AFIP_RUNTIME_REPAIR\afip -Destination C:\AFIP -Recurse -Force
Copy-Item -Path .\AFIP_RUNTIME_REPAIR\tools -Destination C:\AFIP -Recurse -Force
Copy-Item -Path .\AFIP_RUNTIME_REPAIR\tests -Destination C:\AFIP -Recurse -Force
```

The empty `runtime\` directory is intentional. No generated runtime state is overwritten.
