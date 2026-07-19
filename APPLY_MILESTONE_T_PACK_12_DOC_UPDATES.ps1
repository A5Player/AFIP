$ErrorActionPreference = "Stop"

function Add-AppendIfMissing {
    param([string]$Target, [string]$AppendFile, [string]$Marker)
    if (-not (Test-Path $Target)) { throw "Missing target: $Target" }
    if (-not (Test-Path $AppendFile)) { throw "Missing append file: $AppendFile" }
    $content = Get-Content -Raw -Path $Target
    if ($content.Contains($Marker)) {
        Write-Host "Skipped $Target (already updated)"
        return
    }
    Add-Content -Path $Target -Value (Get-Content -Raw -Path $AppendFile)
    Write-Host "Updated $Target"
}

Add-AppendIfMissing "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_12_APPEND.md" "Milestone T Pack 12 - Certified Trade Plan Runtime Orchestration"
Add-AppendIfMissing "HANDOFF.md" "HANDOFF_MILESTONE_T_PACK_12_APPEND.md" "Latest Completed - Milestone T Pack 12"
