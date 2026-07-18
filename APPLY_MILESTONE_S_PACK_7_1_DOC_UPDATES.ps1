$ErrorActionPreference = "Stop"

function Append-Once {
    param([string]$Target, [string]$AppendFile, [string]$Marker)
    $content = Get-Content -Raw -Path $AppendFile
    if ((Test-Path $Target) -and ((Get-Content -Raw -Path $Target) -like "*$Marker*")) {
        Write-Host "Already applied: $Marker"
        return
    }
    Add-Content -Path $Target -Value $content -Encoding UTF8
    Write-Host "Updated: $Target"
}

Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_PACK_7_1_APPEND.md" "Milestone S Pack 7.1 — Position Ceiling Semantics Correction"
Append-Once "HANDOFF.md" "HANDOFF_PACK_7_1_APPEND.md" "Milestone S Pack 7.1 Handoff"
