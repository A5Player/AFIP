$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Add-Once {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$AppendFile,
        [Parameter(Mandatory = $true)][string]$Marker
    )
    if (-not (Test-Path -LiteralPath $Target)) { throw "Missing target: $Target" }
    if (-not (Test-Path -LiteralPath $AppendFile)) { throw "Missing append source: $AppendFile" }
    $existing = Get-Content -LiteralPath $Target -Raw
    $appendContent = Get-Content -LiteralPath $AppendFile -Raw
    if ([string]::IsNullOrWhiteSpace($appendContent)) { throw "Append source is empty: $AppendFile" }
    if ($existing.IndexOf($Marker, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
        Write-Host "Already present: $Target"
        return
    }
    Add-Content -LiteralPath $Target -Value "`r`n$appendContent" -Encoding UTF8
    Write-Host "Appended: $Target"
}

Add-Once -Target (Join-Path $root "AFIP_PROJECT_DATABASE.md") `
    -AppendFile (Join-Path $root "AFIP_PROJECT_DATABASE_PACK_6_5_APPEND.md") `
    -Marker "Milestone S Pack 6.5"

Add-Once -Target (Join-Path $root "HANDOFF.md") `
    -AppendFile (Join-Path $root "HANDOFF_PACK_6_5_APPEND.md") `
    -Marker "Milestone S Pack 6.5 Handoff"

Write-Host "Pack 6.5 documentation updates complete."
