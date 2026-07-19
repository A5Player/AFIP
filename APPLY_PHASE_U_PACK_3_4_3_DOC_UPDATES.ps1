$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Append-Once {
    param(
        [Parameter(Mandatory=$true)][string]$Target,
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Marker
    )
    if (-not (Test-Path $Source)) { throw "Missing source file: $Source" }
    if (-not (Test-Path $Target)) { New-Item -ItemType File -Path $Target -Force | Out-Null }
    $existing = Get-Content $Target -Raw -ErrorAction SilentlyContinue
    if ($null -eq $existing -or $existing -notmatch [regex]::Escape($Marker)) {
        Add-Content -Path $Target -Value "`r`n"
        Get-Content $Source | Add-Content -Path $Target
        Write-Host "Appended $Source to $Target"
    } else {
        Write-Host "Skipped existing marker: $Marker"
    }
}

Append-Once -Target "AFIP_PROJECT_DATABASE.md" -Source "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_4_3_APPEND.md" -Marker "Phase U Pack 3.4.3"
Append-Once -Target "HANDOFF.md" -Source "HANDOFF_PHASE_U_PACK_3_4_3_APPEND.md" -Marker "Phase U Pack 3.4.3"
