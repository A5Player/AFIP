param([string]$ProjectRoot='C:\AFIP')
$ErrorActionPreference='Stop'
Set-Location $ProjectRoot
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if(-not(Test-Path $Python)){$Python='python'}
& $Python -m pytest tests\test_afip_pro_v1_runtime_lifecycle_repair.py tests\test_afip_pro_v1_runtime_continuity.py -q
if($LASTEXITCODE -ne 0){throw "Lifecycle repair validation failed: $LASTEXITCODE"}
Write-Host 'AFIP Pro V1 Runtime Lifecycle Repair validation: PASS'
