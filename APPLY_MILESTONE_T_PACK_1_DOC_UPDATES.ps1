$ErrorActionPreference = "Stop"

function Append-IfMissing {
    param(
        [string]$Target,
        [string]$AppendFile,
        [string]$Marker
    )
    if (-not (Test-Path $Target)) { throw "Missing target: $Target" }
    if (-not (Test-Path $AppendFile)) { throw "Missing append file: $AppendFile" }
    $existing = Get-Content $Target -Raw
    if ($existing -notmatch [regex]::Escape($Marker)) {
        Add-Content -Path $Target -Value (Get-Content $AppendFile -Raw)
        Write-Host "Updated $Target"
    } else {
        Write-Host "Skipped $Target; marker already present"
    }
}

Append-IfMissing "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_PACK_T_1_APPEND.md" "Milestone T Pack 1"
Append-IfMissing "HANDOFF.md" "HANDOFF_PACK_T_1_APPEND.md" "Milestone T Pack 1 Handoff"
