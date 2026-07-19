$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "AFIP Phase U Pack 3.4.9 Direct Overlay"
Write-Host "Files are already overlaid when this ZIP is extracted into the AFIP root."
Write-Host "Running pack validation and real-source collection..."
& .\RUN_PHASE_U_PACK_3_4_9.ps1
