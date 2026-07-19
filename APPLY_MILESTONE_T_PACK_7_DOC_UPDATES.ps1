$ErrorActionPreference = "Stop"
function Append-Once($Target, $AppendFile, $Marker) {
    $content = Get-Content $Target -Raw
    if ($content -match [regex]::Escape($Marker)) {
        Write-Host "Skipped $Target (already updated)"
    } else {
        Add-Content -Path $Target -Value (Get-Content $AppendFile -Raw)
        Write-Host "Updated $Target"
    }
}
Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_7_APPEND.md" "Milestone T Pack 7 — Research-Derived Initial Standard"
Append-Once "HANDOFF.md" "HANDOFF_MILESTONE_T_PACK_7_APPEND.md" "Milestone T Pack 7 Handoff"
