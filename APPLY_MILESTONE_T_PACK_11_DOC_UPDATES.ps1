$ErrorActionPreference = "Stop"

function Append-Once {
    param([string]$Target, [string]$AppendFile, [string]$Marker)
    if (-not (Test-Path $Target)) { throw "Missing target file: $Target" }
    if (-not (Test-Path $AppendFile)) { throw "Missing append file: $AppendFile" }
    $content = Get-Content $Target -Raw
    if ($content -match [regex]::Escape($Marker)) {
        Write-Host "Skipped $Target (already updated)"
        return
    }
    Add-Content -Path $Target -Value "`r`n"
    Get-Content $AppendFile | Add-Content -Path $Target
    Write-Host "Updated $Target"
}

Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_11_APPEND.md" "Milestone T Pack 11"
Append-Once "HANDOFF.md" "HANDOFF_MILESTONE_T_PACK_11_APPEND.md" "Milestone T Pack 11"
