param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference="Stop"
$PackRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$files=Get-Content (Join-Path $PackRoot "FILE_LIST.txt") | Where-Object {$_ -and -not $_.StartsWith('#')}
foreach($relative in $files){
 $source=Join-Path $PackRoot $relative; $target=Join-Path $ProjectRoot $relative
 if(-not(Test-Path $source)){throw "Pack file missing: $relative"}
 $sourceResolved=(Resolve-Path $source).Path
 $targetResolved=$null; if(Test-Path $target){$targetResolved=(Resolve-Path $target).Path}
 if($targetResolved -and $sourceResolved -eq $targetResolved){Write-Host "SKIP self-copy: $relative"; continue}
 New-Item -ItemType Directory -Force (Split-Path -Parent $target) | Out-Null
 Copy-Item -Force $source $target
 Write-Host "Installed: $relative"
}
Write-Host "AFIP V1 Final Integration installed as Patch Only."
