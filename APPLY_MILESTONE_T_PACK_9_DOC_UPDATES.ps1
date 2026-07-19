$ErrorActionPreference = "Stop"
function Append-Once([string]$Target, [string]$AppendFile, [string]$Marker) {
    if (-not (Test-Path $Target)) { throw "Missing target: $Target" }
    if (-not (Test-Path $AppendFile)) { throw "Missing append file: $AppendFile" }
    $current = Get-Content -Raw -Path $Target
    if ($current.Contains($Marker)) {
        Write-Host "Skipped $Target (already updated)"
        return
    }
    Add-Content -Path $Target -Value (Get-Content -Raw -Path $AppendFile)
    Write-Host "Updated $Target"
}
Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_9_APPEND.md" "Milestone T Pack 9"
Append-Once "HANDOFF.md" "HANDOFF_MILESTONE_T_PACK_9_APPEND.md" "Latest Completed — Milestone T Pack 9"
