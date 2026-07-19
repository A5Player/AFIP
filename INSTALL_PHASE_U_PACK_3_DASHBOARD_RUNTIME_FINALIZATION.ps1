$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$Patch = Join-Path $Repo "PATCH"
if (-not (Test-Path (Join-Path $Repo "afip\dashboard_ui"))) { throw "Extract this ZIP directly into the AFIP repository root, for example C:\AFIP" }
if (-not (Test-Path (Join-Path $Patch "afip\dashboard_ui\launcher.py"))) { throw "PATCH payload is missing." }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $Repo "backup\phase_u_pack_3_dashboard_runtime_finalization_$Stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $Backup "afip\dashboard_ui") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Backup "tests") | Out-Null
foreach ($Name in @("launcher.py","__main__.py","home.py")) {
  $Source = Join-Path $Repo "afip\dashboard_ui\$Name"
  if (Test-Path $Source) { Copy-Item $Source (Join-Path $Backup "afip\dashboard_ui\$Name") -Force }
}
$TestPath = Join-Path $Repo "tests\test_phase_u_dashboard_home_runtime_fix.py"
if (Test-Path $TestPath) { Copy-Item $TestPath (Join-Path $Backup "tests\test_phase_u_dashboard_home_runtime_fix.py") -Force }
Copy-Item (Join-Path $Patch "afip\dashboard_ui\launcher.py") (Join-Path $Repo "afip\dashboard_ui\launcher.py") -Force
Copy-Item (Join-Path $Patch "afip\dashboard_ui\__main__.py") (Join-Path $Repo "afip\dashboard_ui\__main__.py") -Force
Copy-Item (Join-Path $Patch "afip\dashboard_ui\home.py") (Join-Path $Repo "afip\dashboard_ui\home.py") -Force
Copy-Item (Join-Path $Patch "tests\test_phase_u_dashboard_home_runtime_fix.py") $TestPath -Force
Get-ChildItem (Join-Path $Repo "afip\dashboard_ui\__pycache__") -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Write-Host "INSTALL PASS" -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host "Next: .\RUN_PHASE_U_PACK_3_DASHBOARD_RUNTIME_FINALIZATION.ps1" -ForegroundColor Cyan
