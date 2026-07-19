$ErrorActionPreference = "Stop"

function Append-Once {
    param([string]$Target, [string]$Source, [string]$Marker)
    if (-not (Test-Path $Target)) { throw "Missing target: $Target" }
    if (-not (Test-Path $Source)) { throw "Missing source: $Source" }
    $content = Get-Content -Raw -Path $Target
    if ($content -match [regex]::Escape($Marker)) {
        Write-Host "Skipped $Target (already updated)"
        return
    }
    Add-Content -Path $Target -Value "`r`n"
    Get-Content -Raw -Path $Source | Add-Content -Path $Target
    Write-Host "Updated $Target"
}

if (Test-Path ".\APPLY_MILESTONE_T_PACK_9_DOC_UPDATES.ps1") {
    & ".\APPLY_MILESTONE_T_PACK_9_DOC_UPDATES.ps1"
}
Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_10_APPEND.md" "Milestone T Pack 10"
Append-Once "HANDOFF.md" "HANDOFF_MILESTONE_T_PACK_10_APPEND.md" "Milestone T Pack 10"
