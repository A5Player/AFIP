AFIP V1 ONE PROCESS PER PROFILE REPAIR

1. Open this ZIP.
2. Copy every file/folder visible here directly into:
   C:\AFIP\source
3. Choose Replace the files in the destination.
4. Run only from C:\AFIP\source:

cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
.\RUN_AFIP_V1_ONE_PROCESS_PER_PROFILE_REPAIR.ps1

Do not run an installer. The ZIP has no extra top-level folder.
