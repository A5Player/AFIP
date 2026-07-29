param([string]$ProjectRoot=$PSScriptRoot)
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = 'python' }

Write-Host 'AFIP SAFE START - verify exact P1-P4 bindings, then delegate to canonical runtime authority...' -ForegroundColor Cyan
& $Python -m tools.afip_verify_account_isolation
if ($LASTEXITCODE -ne 0) {
    Write-Host 'SAFE START BLOCKED - one or more profile bindings are not exact.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host 'Account isolation PASS. Delegating startup to START_AFIP.ps1...' -ForegroundColor Green
& (Join-Path $ProjectRoot 'START_AFIP.ps1') -ProjectRoot $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host 'SAFE START BLOCKED - canonical runtime startup failed.' -ForegroundColor Red
    exit $LASTEXITCODE
}

$statusText = & $Python -m tools.afip_final_integration status --root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host 'SAFE START BLOCKED - canonical runtime status failed.' -ForegroundColor Red
    exit $LASTEXITCODE
}
$status = $statusText | ConvertFrom-Json
if (-not $status.trading.router.running -or -not $status.trading.router.pid) {
    Write-Host 'SAFE START BLOCKED - router process is not running under canonical authority.' -ForegroundColor Red
    exit 3
}

Write-Host ("AFIP CANONICAL RUNTIME RUNNING - Router PID {0}, state {1}" -f $status.trading.router.pid, $status.trading.router.state) -ForegroundColor Green
Write-Host 'Lifecycle Authority: FINAL_INTEGRATION_RUNTIME' -ForegroundColor Yellow
Write-Host 'PowerShell prompt is available. Use STATUS_AFIP.ps1 or STOP_AFIP.ps1.' -ForegroundColor Green
