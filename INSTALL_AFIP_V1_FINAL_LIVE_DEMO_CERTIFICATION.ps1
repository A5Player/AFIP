param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$source = $PSScriptRoot
Get-ChildItem -Path $source -Force | Where-Object { $_.Name -ne "INSTALL_AFIP_V1_FINAL_LIVE_DEMO_CERTIFICATION.ps1" } | ForEach-Object {
    Copy-Item $_.FullName -Destination $ProjectRoot -Recurse -Force
}
Write-Host "AFIP V1 Final Live Demo Certification installed."
