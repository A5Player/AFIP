param([string]$ProjectRoot=$PSScriptRoot)
$ErrorActionPreference='Stop'
Set-Location $ProjectRoot
Write-Host 'AFIP V1 Final Account Isolation & Capital Safety'
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'; if(-not(Test-Path $Python)){$Python='python'}
Write-Host '1/5 Stopping all AFIP execution workers...'
& $Python -m tools.afip_demo_execution_control stop-all | Out-Host
Write-Host '2/5 Installing safety files...'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; $backup=Join-Path $ProjectRoot "backup\AFIP_ACCOUNT_ISOLATION_$stamp"
$files=@(
 'afip\demo_execution_gateway\runtime.py',
 'tools\afip_demo_execution_control.py',
 'tools\afip_verify_account_isolation.py',
 'tools\afip_dashboard_monitor.py',
 'afip\final_integration\dashboard.py',
 'afip\final_integration\runtime.py',
 'config\four_profile_demo.json',
 'tests\test_afip_account_isolation_capital_safety.py'
)
foreach($rel in $files){
 $src=Join-Path $PSScriptRoot $rel; $dst=Join-Path $ProjectRoot $rel
 $srcFull=[IO.Path]::GetFullPath($src); $dstFull=[IO.Path]::GetFullPath($dst)
 if($srcFull -ieq $dstFull){Write-Host "  Already installed: $rel"; continue}
 if(Test-Path $dst){$bak=Join-Path $backup $rel; New-Item -ItemType Directory -Force -Path (Split-Path $bak)|Out-Null; Copy-Item $dst $bak -Force}
 New-Item -ItemType Directory -Force -Path (Split-Path $dst)|Out-Null; Copy-Item $src $dst -Force
 Write-Host "  Installed: $rel"
}
Write-Host '3/5 Clearing stale Python cache...'
Get-ChildItem $ProjectRoot -Directory -Recurse -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host '4/5 Running focused safety tests...'
& $Python -m pytest tests\test_afip_account_isolation_capital_safety.py tests\test_afip_final_account_routing_realtime_ranking_fix.py -q
if($LASTEXITCODE -ne 0){throw 'Focused safety tests failed. AFIP remains STOPPED.'}
Write-Host '5/5 Verifying four-account isolation (read-only; no orders)...'
& $Python -m tools.afip_verify_account_isolation --output runtime\account_isolation_status.json
$verifyExit=$LASTEXITCODE
Write-Host ''
if($verifyExit -eq 0){
 Write-Host 'INSTALLATION COMPLETE - ACCOUNT ISOLATION PASS' -ForegroundColor Green
 Write-Host 'AFIP remains STOPPED by design. Start only with:'
 Write-Host '  .\START_AFIP_SAFE.ps1'
}else{
 Write-Host 'INSTALLATION COMPLETE - ACCOUNT ISOLATION BLOCKED' -ForegroundColor Yellow
 Write-Host 'AFIP remains STOPPED. Review runtime\account_isolation_status.json.'
}
Write-Host 'Capital thresholds: P1=$1000/order, P2=$500/order, P3=$200/order.'
Write-Host "Backup: $backup"
