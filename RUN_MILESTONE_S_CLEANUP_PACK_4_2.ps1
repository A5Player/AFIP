$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== AFIP Milestone S Cleanup Pack 4.2 ==="
Write-Host "Stopping demo runners before patch..."
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match "afip_demo_execution|demo_execution_gateway"
} | ForEach-Object {
    try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch { }
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python venv not found: $python" }

& $python tools\apply_milestone_s_cleanup_pack_4_2.py
if ($LASTEXITCODE -ne 0) { throw "Pack 4.2 patch application failed." }

Get-ChildItem -Path $PSScriptRoot -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $PSScriptRoot -Recurse -File -Include *.pyc -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $PSScriptRoot ".pytest_cache") -ErrorAction SilentlyContinue

& $python -m pytest tests\test_milestone_s_cleanup_pack_4_2.py tests\test_production_sprint8_real_confidence_calibration.py tests\phase2\test_afip_intelligence_naming.py -v
if ($LASTEXITCODE -ne 0) { throw "Pack 4.2 focused regression failed." }

Write-Host ""
Write-Host "Pack 4.2 focused regression completed. Execution remains STOPPED."
Write-Host "Next: run full pytest and AFIP Local Quality Check."
