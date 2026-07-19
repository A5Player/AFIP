$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Append-Once {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Marker
    )
    if (-not (Test-Path $Source)) { throw "Missing append source: $Source" }
    if (-not (Test-Path $Target)) { New-Item -ItemType File -Path $Target | Out-Null }
    $current = Get-Content $Target -Raw -ErrorAction SilentlyContinue
    if ($current -and $current.Contains($Marker)) {
        Write-Host "Already present in $Target"
        return
    }
    Add-Content -Path $Target -Value (Get-Content $Source -Raw) -Encoding UTF8
    Write-Host "Appended $Source to $Target"
}

Append-Once -Target "AFIP_PROJECT_DATABASE.md" -Source "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_4_1_APPEND.md" -Marker "Phase U Pack 3.4.1"
Append-Once -Target "HANDOFF.md" -Source "HANDOFF_PHASE_U_PACK_3_4_1_APPEND.md" -Marker "Phase U Pack 3.4.1 Handoff"
