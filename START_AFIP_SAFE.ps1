$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host 'AFIP SAFE START - exact P1-P4 verification and confirmed sequential router startup...' -ForegroundColor Cyan

& .\.venv\Scripts\python.exe -m tools.afip_verify_account_isolation
if ($LASTEXITCODE -ne 0) {
    Write-Host 'SAFE START BLOCKED - one or more profile bindings are not exact.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host 'Account isolation PASS. Starting one sequential MT5 router...' -ForegroundColor Green
$output = & .\.venv\Scripts\python.exe -m tools.afip_demo_execution_control start-all 2>&1
$code = $LASTEXITCODE
$output | Write-Host
if ($code -ne 0) {
    Write-Host 'SAFE START BLOCKED - router did not complete its startup handshake. See runtime\execution\sequential_router.log.' -ForegroundColor Red
    exit $code
}

$statusText = & .\.venv\Scripts\python.exe -m tools.afip_demo_execution_control status
$status = $statusText | ConvertFrom-Json
if (-not $status.router.running -or -not $status.router.pid) {
    Write-Host 'SAFE START BLOCKED - router process is not running.' -ForegroundColor Red
    exit 3
}

Write-Host ("AFIP ROUTER RUNNING - PID {0}, state {1}, concurrent workers 0" -f $status.router.pid, $status.router.state) -ForegroundColor Green
Write-Host 'PowerShell prompt is available. Use STATUS_AFIP.ps1 or demo execution status.' -ForegroundColor Green
