param([Parameter(Mandatory=$true)][string]$ProjectRoot)
$ErrorActionPreference='Stop';$PackRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
if(-not(Test-Path (Join-Path $ProjectRoot 'afip'))){throw "Invalid AFIP repository: $ProjectRoot"}
$Files=Get-Content (Join-Path $PackRoot 'FILE_LIST_AFIP_V1_FINAL_CONSOLIDATION.txt') | Where-Object {$_ -and -not $_.StartsWith('#')}
$BackupRoot=Join-Path $ProjectRoot ('runtime\installation_backups\v1_final_consolidation_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
foreach($Relative in $Files){
 if($Relative -eq 'INSTALL_AFIP_V1_FINAL_CONSOLIDATION.ps1'){continue}
 $Source=Join-Path $PackRoot $Relative;$Target=Join-Path $ProjectRoot $Relative
 if(-not(Test-Path $Source)){throw "Missing pack file: $Relative"}
 if(Test-Path $Target){$Backup=Join-Path $BackupRoot $Relative;New-Item -ItemType Directory -Force (Split-Path -Parent $Backup)|Out-Null;Copy-Item -Force $Target $Backup}
 New-Item -ItemType Directory -Force (Split-Path -Parent $Target)|Out-Null;Copy-Item -Force $Source $Target;Write-Host "Installed: $Relative"
}
Write-Host "Backup: $BackupRoot";Write-Host 'AFIP V1 Final Consolidation installed as Patch Only.'
