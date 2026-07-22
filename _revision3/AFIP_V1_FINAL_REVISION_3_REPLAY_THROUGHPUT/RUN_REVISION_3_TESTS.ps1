param(
    [string]$ProjectRoot = "C:\AFIP\source"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . ".\.venv\Scripts\Activate.ps1"
}

python -m pytest `
    tests\test_revision_3_replay_throughput.py `
    tests\test_phase_u_pack_3_2_automatic_research_runtime.py `
    tests\test_milestone_t_pack_3_historical_replay_runner.py `
    -v

python tools\afip_local_quality_check.py
