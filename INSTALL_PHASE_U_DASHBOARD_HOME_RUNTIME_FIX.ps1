$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = (Get-Location).Path

if (-not (Test-Path (Join-Path $Target "afip\dashboard_ui"))) {
    throw "Run this installer from the AFIP repository root, for example C:\AFIP"
}

$Backup = Join-Path $Target ("backup\phase_u_dashboard_home_runtime_fix_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path (Join-Path $Backup "afip\dashboard_ui") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Backup "tests") | Out-Null

foreach ($Name in @("launcher.py", "__main__.py", "home.py")) {
    $Existing = Join-Path $Target ("afip\dashboard_ui\" + $Name)
    if (Test-Path $Existing) { Copy-Item $Existing (Join-Path $Backup ("afip\dashboard_ui\" + $Name)) -Force }
}
$ExistingTest = Join-Path $Target "tests\test_phase_u_dashboard_home_runtime_fix.py"
if (Test-Path $ExistingTest) { Copy-Item $ExistingTest (Join-Path $Backup "tests\test_phase_u_dashboard_home_runtime_fix.py") -Force }

Copy-Item (Join-Path $Root "afip\dashboard_ui\launcher.py") (Join-Path $Target "afip\dashboard_ui\launcher.py") -Force
Copy-Item (Join-Path $Root "afip\dashboard_ui\__main__.py") (Join-Path $Target "afip\dashboard_ui\__main__.py") -Force
Copy-Item (Join-Path $Root "afip\dashboard_ui\home.py") (Join-Path $Target "afip\dashboard_ui\home.py") -Force
Copy-Item (Join-Path $Root "tests\test_phase_u_dashboard_home_runtime_fix.py") (Join-Path $Target "tests\test_phase_u_dashboard_home_runtime_fix.py") -Force

Get-ChildItem (Join-Path $Target "afip\dashboard_ui\__pycache__") -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse
Write-Host "Patch installed. Backup: $Backup" -ForegroundColor Green
Write-Host "Next: .\RUN_PHASE_U_DASHBOARD_HOME_RUNTIME_FIX.ps1" -ForegroundColor Cyan
