param([string]$ProjectRoot=$PSScriptRoot)
$ErrorActionPreference='Stop'
Set-Location $ProjectRoot
Write-Host 'AFIP V1 Final Account Routing, Realtime Dashboard & Ranking Fix'
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'; if(-not(Test-Path $Python)){$Python='python'}
Write-Host '1/5 Stopping AFIP safely...'
& $Python -m tools.afip_final_integration stop --root $ProjectRoot | Out-Host
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; $backup=Join-Path $ProjectRoot "backup\AFIP_FINAL_ROUTING_FIX_$stamp"
Write-Host '2/5 Backing up and installing patch files...'
$files=@(
'afip\final_integration\dashboard.py',
'afip\final_integration\runtime.py',
'afip\demo_execution_gateway\runtime.py',
'tools\afip_demo_execution_control.py',
'tools\afip_dashboard_monitor.py'
)
foreach($rel in $files){
 $src=Join-Path $PSScriptRoot $rel; $dst=Join-Path $ProjectRoot $rel
 $srcFull=[IO.Path]::GetFullPath($src); $dstFull=[IO.Path]::GetFullPath($dst)
 if($srcFull -ieq $dstFull){Write-Host "  Already installed: $rel"; continue}
 if(Test-Path $dst){$bak=Join-Path $backup $rel; New-Item -ItemType Directory -Force -Path (Split-Path $bak) | Out-Null; Copy-Item $dst $bak -Force}
 New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null; Copy-Item $src $dst -Force
 Write-Host "  Installed: $rel"
}
Write-Host '3/5 Clearing stale Python cache and generated dashboards...'
Get-ChildItem $ProjectRoot -Directory -Recurse -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $ProjectRoot 'runtime\dashboard\*.html') -Force -ErrorAction SilentlyContinue
Write-Host '4/5 Starting isolated P1-P4 runtime and 2-second dashboard monitor...'
$result=& $Python -m tools.afip_final_integration start --root $ProjectRoot
$result | Out-Host
if($LASTEXITCODE -ne 0){throw "AFIP start failed: $LASTEXITCODE"}
if($result -match 'profile_isolation_validation_failed'){throw 'AFIP blocked start because profile account/terminal mapping is not isolated. Check AFIP_P1_LOGIN through AFIP_P4_LOGIN and terminal folders.'}
Write-Host '5/5 Opening production dashboard...'
$dashboard=Join-Path $ProjectRoot 'runtime\dashboard\afip_dashboard.html'
Start-Sleep -Seconds 3
if(Test-Path $dashboard){Start-Process $dashboard}
Write-Host ''
Write-Host 'AFIP FINAL ROUTING FIX INSTALLED AND STARTED'
Write-Host 'Dashboard refresh: 2 seconds (background, non-blocking)'
Write-Host 'Research ranking page: runtime\dashboard\afip_research_data_dashboard.html'
Write-Host 'Safety: duplicate accounts or wrong terminal binding are blocked before order_send.'
Write-Host "Backup: $backup"
