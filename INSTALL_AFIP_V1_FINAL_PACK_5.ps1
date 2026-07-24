param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
$PackRoot = $PSScriptRoot
Copy-Item -Force "$PackRoot\tools\afip_v1_pack_5_repository_cleanup.py" "$ProjectRoot\tools\"
Copy-Item -Force "$PackRoot\tools\afip_v1_pack_5_final_runtime_certification.py" "$ProjectRoot\tools\"
Copy-Item -Force "$PackRoot\tests\test_afip_v1_pack_5_final_cleanup_certification.py" "$ProjectRoot\tests\"
Copy-Item -Force "$PackRoot\RUN_AFIP_V1_FINAL_PACK_5.ps1" "$ProjectRoot\"
Copy-Item -Force "$PackRoot\RUN_AFIP_V1_FINAL_PACK_5.bat" "$ProjectRoot\"
Write-Host "AFIP V1 Final Pack 5 installed."
