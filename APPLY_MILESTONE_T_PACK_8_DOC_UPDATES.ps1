$ErrorActionPreference = "Stop"
function Append-Once([string]$Target, [string]$Source, [string]$Marker) {
    $content = Get-Content $Target -Raw
    if ($content -match [regex]::Escape($Marker)) { Write-Host "Skipped $Target (already updated)"; return }
    Add-Content -Path $Target -Value "`r`n"
    Get-Content $Source -Raw | Add-Content -Path $Target
    Write-Host "Updated $Target"
}
# Repair the missed Pack 7 documentation first.
& .\APPLY_MILESTONE_T_PACK_7_DOC_UPDATES.ps1
Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_8_APPEND.md" "Milestone T Pack 8"
Append-Once "HANDOFF.md" "HANDOFF_MILESTONE_T_PACK_8_APPEND.md" "Milestone T Pack 8"
