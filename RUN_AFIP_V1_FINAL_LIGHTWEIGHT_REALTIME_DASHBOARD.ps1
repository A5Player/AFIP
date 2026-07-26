param([string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
if (Test-Path ".\.venv\Scripts\Activate.ps1") { . ".\.venv\Scripts\Activate.ps1" }
python -m pytest tests\test_afip_v1_final_lightweight_realtime_dashboard.py tests\test_afip_v1_final_runtime_consistency_patch.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "AFIP V1 Final Lightweight Realtime Dashboard focused certification: PASS"
