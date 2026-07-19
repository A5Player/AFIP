$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$BundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetRoot = "C:\AFIP"

if (-not (Test-Path $TargetRoot)) { throw "AFIP repository not found: $TargetRoot" }

$packs = @("3_4_2", "3_4_3", "3_4_4", "3_4_5", "3_4_6", "3_4_7")
foreach ($pack in $packs) {
    $source = Join-Path $BundleRoot "PACK_$pack"
    Write-Host "Installing Pack $pack"
    Get-ChildItem -Path $source -Force | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $TargetRoot -Recurse -Force
    }
}
Write-Host "All Phase U Pack 3.4.2 to 3.4.7 files installed."
Write-Host "Run VALIDATE_ALL_PHASE_U_PACK_3_4_2_TO_3_4_7.ps1 from C:\AFIP."
