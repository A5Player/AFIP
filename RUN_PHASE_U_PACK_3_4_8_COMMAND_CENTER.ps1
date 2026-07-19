$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $Python = ".\.venv\Scripts\python.exe"
}

Write-Host "=== AFIP Phase U Pack 3.4.8 Command Center ===" -ForegroundColor Cyan

& $Python -m pytest "tests/test_phase_u_pack_3_4_8_command_center.py" -q
if ($LASTEXITCODE -ne 0) {
    throw "Pack regression test failed with exit code $LASTEXITCODE"
}

& $Python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) {
    throw "Dashboard generation failed with exit code $LASTEXITCODE"
}

$DashboardHome = Join-Path $Root "runtime\dashboard\afip_dashboard.html"
if (-not (Test-Path $DashboardHome)) {
    throw "Dashboard home was not generated: $DashboardHome"
}

$DashboardContent = Get-Content -Path $DashboardHome -Raw
$ExpectedItems = @(
    "AFIP Command Center",
    "afip_profiles_dashboard.html",
    "afip_intelligence_engine_dashboard.html",
    "afip_research_data_dashboard.html"
)

foreach ($ExpectedItem in $ExpectedItems) {
    if ($DashboardContent -notmatch [regex]::Escape($ExpectedItem)) {
        throw "Missing expected command center content: $ExpectedItem"
    }
}

Write-Host "PHASE U PACK 3.4.8 COMMAND CENTER: PASS" -ForegroundColor Green
Write-Host ("Open: " + $DashboardHome)
