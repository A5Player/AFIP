$ErrorActionPreference = "Stop"
function Append-Once($Target, $Source, $Marker) {
    if (-not (Test-Path $Target)) { New-Item -ItemType File -Path $Target -Force | Out-Null }
    $text = Get-Content $Target -Raw
    if ($text -notmatch [regex]::Escape($Marker)) {
        Add-Content $Target "`r`n"
        Get-Content $Source | Add-Content $Target
        Write-Host "Updated $Target"
    } else { Write-Host "Already updated $Target" }
}
Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_14_APPEND.md" "Milestone T Pack 14"
Append-Once "HANDOFF.md" "HANDOFF_MILESTONE_T_PACK_14_APPEND.md" "Milestone T Pack 14"
