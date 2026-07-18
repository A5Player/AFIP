$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== AFIP Milestone S Cleanup Pack 4.1 ==="
Write-Host "Stopping demo runners before patch..."
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match "afip_demo_execution|demo_execution_gateway"
} | ForEach-Object {
    try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch { }
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python venv not found: $python" }

& $python tools\apply_milestone_s_cleanup_pack_4_1.py
& $python -m pytest tests\test_milestone_s_cleanup_pack_4_1.py -v

Write-Host ""
Write-Host "Pack 4.1 focused tests completed. Execution remains STOPPED."
Write-Host "Next: run full pytest before demo re-arming."
