$ErrorActionPreference = "Stop"
Write-Host "AFIP V1 Final Revision 2 - Replay Performance Certification"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "AFIP virtual environment not found: $python" }

& $python -m pytest -q `
  tests/test_milestone_t_pack_3_historical_replay_runner.py `
  tests/test_afip_v1_final_runtime_observatory.py `
  tests/test_afip_v1_final_revision_2_replay_performance.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nGit review"
git status
git diff --name-only
git diff --cached --name-only
