AFIP V1 Final Source Merge Repair

Copy files preserving paths into C:\AFIP\source.

Run:
cd C:\AFIP\source
.\.venv\Scripts\Activate.ps1
python -m pytest -q

Verify:
git diff --stat
git status
