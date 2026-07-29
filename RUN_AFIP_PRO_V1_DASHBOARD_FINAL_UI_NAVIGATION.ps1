param([string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
& $python -m py_compile afip\dashboard_ui\navigation.py afip\dashboard_ui\split_runtime.py
if ($LASTEXITCODE -ne 0) { throw "Python compile failed" }
& $python -m pytest tests\test_afip_pro_v1_dashboard_final_navigation.py -q
if ($LASTEXITCODE -ne 0) { throw "Focused regression failed" }
& $python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw "Dashboard generation failed" }
$profile = Join-Path $ProjectRoot "runtime\dashboard\afip_profiles_dashboard.html"
$html = Get-Content $profile -Raw
if ($html -notmatch "afip-standalone-sidebar" -or $html -notmatch "Dashboard Navigation") { throw "Generated sidebar evidence missing" }
Write-Host "AFIP Pro V1 Dashboard Final UI Navigation: PASS"
