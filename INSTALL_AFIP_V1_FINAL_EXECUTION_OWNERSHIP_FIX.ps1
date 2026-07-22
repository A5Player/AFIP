param([string]$ProjectRoot=$PSScriptRoot)
$ErrorActionPreference='Stop'
Set-Location $ProjectRoot
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if(-not(Test-Path $Python)){$Python='python'}
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Backup=Join-Path $ProjectRoot "backup\AFIP_V1_EXECUTION_OWNERSHIP_$Stamp"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null

Write-Host 'AFIP V1 Final Execution Ownership Fix' -ForegroundColor Cyan
Write-Host '1/5 Stopping all execution workers...'
& $Python -m tools.afip_demo_execution_control stop-all | Out-Host
Remove-Item (Join-Path $ProjectRoot 'runtime\execution\account_routing.lock') -Force -ErrorAction SilentlyContinue

$Files=@(
 'afip\demo_execution_gateway\runtime.py',
 'tools\afip_demo_execution_control.py',
 'tools\afip_verify_account_isolation.py',
 'tests\test_afip_final_execution_ownership.py',
 'START_AFIP_SAFE.ps1',
 'STOP_AFIP_EMERGENCY.ps1'
)
Write-Host '2/5 Backing up and installing files...'
foreach($Rel in $Files){
  $Source=Join-Path $PSScriptRoot $Rel
  $Target=Join-Path $ProjectRoot $Rel
  $SourceFull=[IO.Path]::GetFullPath($Source)
  $TargetFull=[IO.Path]::GetFullPath($Target)
  if(Test-Path $Target){
    $BackupTarget=Join-Path $Backup $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path $BackupTarget -Parent) | Out-Null
    Copy-Item $Target $BackupTarget -Force
  }
  if($SourceFull -ieq $TargetFull){
    Write-Host "  Already installed: $Rel"
    continue
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $Target -Parent) | Out-Null
  Copy-Item $Source $Target -Force
  Write-Host "  Installed: $Rel"
}

Write-Host '3/5 Removing stale Python cache...'
Get-ChildItem -Path (Join-Path $ProjectRoot 'afip\demo_execution_gateway') -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path (Join-Path $ProjectRoot 'tools') -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

Write-Host '4/5 Running focused safety tests...'
& $Python -m pytest tests\test_afip_final_execution_ownership.py -q
if($LASTEXITCODE -ne 0){throw 'Execution ownership tests failed. AFIP remains stopped.'}

Write-Host '5/5 Running read-only account isolation verification...'
& $Python -m tools.afip_verify_account_isolation --output runtime\account_isolation_status.json
if($LASTEXITCODE -ne 0){throw 'Account isolation verification failed. AFIP remains stopped.'}

Write-Host ''
Write-Host 'EXECUTION OWNERSHIP FIX INSTALLED - AFIP REMAINS STOPPED' -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host 'Enable Algo Trading only after reviewing the PASS result, then run .\START_AFIP_SAFE.ps1'
