$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$Root = (Get-Location).Path
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Backup = Join-Path $Root "backup\AFIP_V1_FINAL_SEQUENTIAL_MT5_ROUTING_FIX_$Stamp"
Write-Host 'AFIP V1 Final Sequential MT5 Routing Fix' -ForegroundColor Cyan
Write-Host '1/5 Stopping all current and legacy execution workers...' -ForegroundColor Yellow
try { & .\.venv\Scripts\python.exe -m tools.afip_demo_execution_control stop-all | Out-Host } catch {}
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'DemoExecutionRunner|afip_profile_sequential_execution_router' } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force } catch {} }
Write-Host '2/5 Backing up affected files...' -ForegroundColor Yellow
$Files = @(
 'afip\demo_execution_gateway\runtime.py',
 'tools\afip_demo_execution_control.py',
 'tools\afip_profile_sequential_execution_router.py',
 'tools\afip_verify_account_isolation.py',
 'START_AFIP_SAFE.ps1',
 'STOP_AFIP_EMERGENCY.ps1'
)
foreach ($Rel in $Files) {
  $Target = Join-Path $Root $Rel
  if (Test-Path $Target) {
    $Dest = Join-Path $Backup $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path $Dest) | Out-Null
    Copy-Item $Target $Dest -Force
  }
}
Write-Host '3/5 Removing stale P1-P4 worker PID files and cached bindings...' -ForegroundColor Yellow
Remove-Item runtime\profiles\p*\demo_runner.pid -Force -ErrorAction SilentlyContinue
Remove-Item runtime\execution\sequential_router.pid -Force -ErrorAction SilentlyContinue
Get-ChildItem afip,tools -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host '4/5 Running focused regression tests...' -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pytest tests\test_afip_sequential_profile_router.py tests\test_afip_final_execution_ownership.py -q
if ($LASTEXITCODE -ne 0) { throw 'Focused regression failed; AFIP remains stopped.' }
Write-Host '5/5 Verifying P1-P4 exact terminal/login/server bindings (read-only)...' -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m tools.afip_verify_account_isolation
if ($LASTEXITCODE -ne 0) { throw 'Account isolation verification failed; AFIP remains stopped.' }
Write-Host ''
Write-Host 'SEQUENTIAL MT5 ROUTING FIX INSTALLED - AFIP REMAINS STOPPED' -ForegroundColor Green
Write-Host 'Review all four bindings, then run: .\START_AFIP_SAFE.ps1' -ForegroundColor Cyan
Write-Host "Backup: $Backup"
