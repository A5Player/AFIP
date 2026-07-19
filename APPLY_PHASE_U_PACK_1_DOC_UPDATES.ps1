$ErrorActionPreference="Stop"
Get-Content .\AFIP_PROJECT_DATABASE_PHASE_U_PACK_1_APPEND.md | Add-Content .\AFIP_PROJECT_DATABASE.md
Get-Content .\HANDOFF_PHASE_U_PACK_1_APPEND.md | Add-Content .\HANDOFF.md
Write-Host "Updated AFIP_PROJECT_DATABASE.md and HANDOFF.md"
