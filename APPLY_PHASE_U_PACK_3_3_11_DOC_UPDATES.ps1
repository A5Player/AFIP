param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

function Append-Once {
    param([string]$Target, [string]$Source, [string]$Marker)
    if (-not (Test-Path $Source)) { throw "Missing source: $Source" }
    if (-not (Test-Path $Target)) { New-Item -ItemType File -Path $Target -Force | Out-Null }
    $existing = Get-Content $Target -Raw
    if ($existing -notmatch [regex]::Escape($Marker)) {
        Add-Content -Path $Target -Value (Get-Content $Source -Raw)
        Write-Host "Appended $Source to $Target" -ForegroundColor Green
    } else {
        Write-Host "Already present in $Target" -ForegroundColor DarkYellow
    }
}

Append-Once -Target "AFIP_PROJECT_DATABASE.md" -Source "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_3_11_APPEND.md" -Marker "Phase U Pack 3.3.11"
Append-Once -Target "HANDOFF.md" -Source "HANDOFF_PHASE_U_PACK_3_3_11_APPEND.md" -Marker "Phase U Pack 3.3.11 Handoff"
