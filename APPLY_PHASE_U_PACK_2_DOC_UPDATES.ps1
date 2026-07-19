$ErrorActionPreference = "Stop"
function Append-Once($Target, $AppendFile, $Marker) {
    if (-not (Test-Path $Target)) { New-Item -ItemType File -Path $Target -Force | Out-Null }
    $content = Get-Content $Target -Raw
    if ($content -notmatch [regex]::Escape($Marker)) {
        Add-Content -Path $Target -Value "`r`n"
        Get-Content $AppendFile | Add-Content -Path $Target
        Write-Host "Updated $Target"
    } else { Write-Host "Already updated: $Target" }
}
Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_PHASE_U_PACK_2_APPEND.md" "Phase U Pack 2 — Two Separate Dashboards"
Append-Once "HANDOFF.md" "HANDOFF_PHASE_U_PACK_2_APPEND.md" "Phase U Pack 2 — Two Separate Dashboards"
