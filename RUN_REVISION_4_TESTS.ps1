param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
& $python -m pytest tests\test_revision_4_research_separation.py tests\test_revision_3_replay_throughput.py tests\test_phase_u_pack_3_2_automatic_research_runtime.py tests\test_milestone_t_pack_3_historical_replay_runner.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python tools\afip_local_quality_check.py
exit $LASTEXITCODE
