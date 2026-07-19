$ErrorActionPreference = "Stop"
if (Test-Path "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_APPEND.md") { Get-Content "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_APPEND.md" | Add-Content "AFIP_PROJECT_DATABASE.md" }
if (Test-Path "HANDOFF_PHASE_U_PACK_3_APPEND.md") { Get-Content "HANDOFF_PHASE_U_PACK_3_APPEND.md" | Add-Content "HANDOFF.md" }
Write-Host "Updated AFIP_PROJECT_DATABASE.md and HANDOFF.md"
