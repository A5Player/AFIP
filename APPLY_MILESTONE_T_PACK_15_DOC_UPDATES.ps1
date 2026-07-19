$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
function Append-Once([string]$Target, [string]$Source, [string]$Marker) {
    $targetPath = Join-Path $root $Target
    $sourcePath = Join-Path $root $Source
    if (-not (Test-Path $targetPath)) { New-Item -ItemType File -Path $targetPath -Force | Out-Null }
    $content = Get-Content $targetPath -Raw
    if ($content -notmatch [regex]::Escape($Marker)) {
        Add-Content -Path $targetPath -Value (Get-Content $sourcePath -Raw)
        Write-Host "Updated $Target"
    } else { Write-Host "$Target already contains Pack 15 update" }
}
Append-Once "AFIP_PROJECT_DATABASE.md" "AFIP_PROJECT_DATABASE_MILESTONE_T_PACK_15_APPEND.md" "Milestone T Pack 15"
Append-Once "HANDOFF.md" "HANDOFF_MILESTONE_T_PACK_15_APPEND.md" "Milestone T Final Handoff"
