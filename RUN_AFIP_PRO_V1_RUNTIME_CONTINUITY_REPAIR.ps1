param([string]$ProjectRoot = "C:\AFIP")
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = 'python' }
& $Python -m pytest tests\test_afip_pro_v1_runtime_continuity.py -v
if ($LASTEXITCODE -ne 0) { throw "Focused runtime continuity validation failed: $LASTEXITCODE" }
& $Python -m py_compile afip\final_integration\runtime.py tools\afip_runtime_continuity_watchdog.py
if ($LASTEXITCODE -ne 0) { throw "Python compile validation failed: $LASTEXITCODE" }
Write-Host "AFIP Pro V1 Runtime Continuity Repair validation: PASS"
