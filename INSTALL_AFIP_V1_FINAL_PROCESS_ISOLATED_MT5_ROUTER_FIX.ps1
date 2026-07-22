$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host 'AFIP V1 Final Process-Isolated MT5 Router Fix' -ForegroundColor Cyan

$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Python venv not found: $python" }

Write-Host '1/5 Stopping AFIP execution...' -ForegroundColor Yellow
& $python -m tools.afip_demo_execution_control stop-all

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path $PSScriptRoot "backup\AFIP_V1_FINAL_PROCESS_ISOLATED_MT5_ROUTER_FIX_$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

Write-Host '2/5 Backing up affected files...' -ForegroundColor Yellow
$files = @(
  'tools\afip_demo_execution_control.py',
  'tools\afip_profile_sequential_execution_router.py',
  'tools\afip_profile_execution_once.py',
  'tools\afip_verify_account_isolation.py',
  'START_AFIP_SAFE.ps1'
)
foreach ($file in $files) {
  $source = Join-Path $PSScriptRoot $file
  if (Test-Path $source) {
    $target = Join-Path $backup $file
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    Copy-Item -Force $source $target
  }
}

Write-Host '3/5 Removing stale router/profile state and Python cache...' -ForegroundColor Yellow
Remove-Item -Force -ErrorAction SilentlyContinue 'runtime\execution\sequential_router.pid'
Remove-Item -Force -ErrorAction SilentlyContinue 'runtime\execution\sequential_router_status.json'
Remove-Item -Force -ErrorAction SilentlyContinue 'runtime\execution\account_routing.lock'
Get-ChildItem -Path 'runtime\profiles' -Recurse -Filter 'demo_runner.pid' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path 'tools','afip','tests' -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host '4/5 Running focused regression tests...' -ForegroundColor Yellow
& $python -m pytest tests\test_afip_process_isolated_router.py tests\test_afip_sequential_router_startup.py -q
if ($LASTEXITCODE -ne 0) { throw 'Focused regression tests failed.' }

Write-Host '5/5 Verifying exact P1-P4 bindings (read-only)...' -ForegroundColor Yellow
& $python -m tools.afip_verify_account_isolation
if ($LASTEXITCODE -ne 0) { throw 'Account isolation verification failed.' }

Write-Host ''
Write-Host 'PROCESS-ISOLATED MT5 ROUTER FIX INSTALLED - AFIP REMAINS STOPPED' -ForegroundColor Green
Write-Host 'Run: .\START_AFIP_SAFE.ps1' -ForegroundColor Green
Write-Host "Backup: $backup" -ForegroundColor DarkGray
