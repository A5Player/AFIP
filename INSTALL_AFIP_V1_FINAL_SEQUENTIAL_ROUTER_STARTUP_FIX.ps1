$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$Root = (Get-Location).Path
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Backup = Join-Path $Root "backup\AFIP_V1_FINAL_SEQUENTIAL_ROUTER_STARTUP_FIX_$Stamp"

Write-Host 'AFIP V1 Final Sequential Router Startup Fix' -ForegroundColor Cyan
Write-Host '1/5 Stopping AFIP execution...' -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m tools.afip_demo_execution_control stop-all | Out-Host

Write-Host '2/5 Backing up affected files...' -ForegroundColor Yellow
$Files = @(
  'tools\afip_demo_execution_control.py',
  'tools\afip_profile_sequential_execution_router.py',
  'START_AFIP_SAFE.ps1'
)
foreach ($Relative in $Files) {
  $Target = Join-Path $Root $Relative
  if (Test-Path $Target) {
    $BackupTarget = Join-Path $Backup $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path $BackupTarget) | Out-Null
    Copy-Item -LiteralPath $Target -Destination $BackupTarget -Force
  }
}

Write-Host '3/5 Removing stale router PID/state and Python cache...' -ForegroundColor Yellow
Remove-Item -Force -ErrorAction SilentlyContinue runtime\execution\sequential_router.pid
Get-ChildItem -Path tools,afip -Directory -Recurse -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host '4/5 Running focused regression tests...' -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pytest tests\test_afip_sequential_profile_router.py tests\test_afip_sequential_router_startup.py -q
if ($LASTEXITCODE -ne 0) { throw 'Focused regression failed.' }

Write-Host '5/5 Verifying exact P1-P4 bindings (read-only)...' -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m tools.afip_verify_account_isolation
if ($LASTEXITCODE -ne 0) { throw 'Account isolation verification failed.' }

Write-Host ''
Write-Host 'SEQUENTIAL ROUTER STARTUP FIX INSTALLED - AFIP REMAINS STOPPED' -ForegroundColor Green
Write-Host 'Run: .\START_AFIP_SAFE.ps1' -ForegroundColor Green
Write-Host "Backup: $Backup"
