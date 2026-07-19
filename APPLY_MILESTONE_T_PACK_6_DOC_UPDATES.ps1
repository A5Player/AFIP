$ErrorActionPreference = "Stop"

function Append-Once {
    param(
        [string]$Target,
        [string]$AppendFile,
        [string]$Marker
    )

    if (-not (Test-Path $Target)) {
        throw "Missing target document: $Target"
    }
    if (-not (Test-Path $AppendFile)) {
        throw "Missing append document: $AppendFile"
    }

    $content = Get-Content $Target -Raw
    if ($content.Contains($Marker)) {
        Write-Host "Skipped $Target (already updated)"
        return
    }

    Add-Content -Path $Target -Value (Get-Content $AppendFile -Raw)
    Write-Host "Updated $Target"
}

Append-Once -Target "AFIP_PROJECT_DATABASE.md" -AppendFile "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_6_APPEND.md" -Marker "Milestone T Pack 6 — Robustness"
Append-Once -Target "HANDOFF.md" -AppendFile "HANDOFF_MILESTONE_T_PACK_6_APPEND.md" -Marker "Milestone T Pack 6 Handoff"
