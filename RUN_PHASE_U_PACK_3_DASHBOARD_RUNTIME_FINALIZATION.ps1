$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Repo
$Python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
& $Python -m pytest tests/test_phase_u_dashboard_home_runtime_fix.py -q
if ($LASTEXITCODE -ne 0) { throw "Pack tests failed." }
$watch = [System.Diagnostics.Stopwatch]::StartNew()
& $Python -m afip.dashboard_ui
$code = $LASTEXITCODE
$watch.Stop()
if ($code -ne 0) { throw "Dashboard generation failed with exit code $code" }
if ($watch.Elapsed.TotalSeconds -gt 60) { throw "Dashboard generation exceeded 60 seconds: $($watch.Elapsed.TotalSeconds)" }
$Required = @(
 "runtime\dashboard\afip_dashboard.html",
 "runtime\dashboard\afip_profiles_dashboard.html",
 "runtime\dashboard\afip_intelligence_engine_dashboard.html",
 "runtime\dashboard\afip_research_data_dashboard.html"
)
foreach ($File in $Required) { if (-not (Test-Path $File)) { throw "Missing generated file: $File" } }
Write-Host "PHASE U PACK 3 DASHBOARD RUNTIME FINALIZATION: PASS" -ForegroundColor Green
Write-Host "Dashboard command returned in $([math]::Round($watch.Elapsed.TotalSeconds,2)) seconds."
Write-Host "Open: C:\AFIP\runtime\dashboard\afip_dashboard.html" -ForegroundColor Cyan
