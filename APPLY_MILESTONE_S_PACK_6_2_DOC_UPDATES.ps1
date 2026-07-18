$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dbAppend = Join-Path $root "AFIP_PROJECT_DATABASE_PACK_6_2_APPEND.md"
$handoffAppend = Join-Path $root "HANDOFF_PACK_6_2_APPEND.md"

function Add-Once {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Target,

        [Parameter(Mandatory = $true)]
        [string]$AppendFile,

        [Parameter(Mandatory = $true)]
        [string]$Marker
    )

    if (-not (Test-Path -LiteralPath $Target)) {
        throw "Missing target: $Target"
    }

    if (-not (Test-Path -LiteralPath $AppendFile)) {
        throw "Missing append source: $AppendFile"
    }

    $existing = Get-Content -LiteralPath $Target -Raw
    $appendContent = Get-Content -LiteralPath $AppendFile -Raw

    if ([string]::IsNullOrWhiteSpace($appendContent)) {
        throw "Append source is empty: $AppendFile"
    }

    if ($existing.IndexOf($Marker, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
        Write-Host "Already present: $Target"
        return
    }

    Add-Content -LiteralPath $Target -Value "`r`n$appendContent" -Encoding UTF8
    Write-Host "Appended: $Target"
}

# Use ASCII-only markers for Windows PowerShell 5.1 compatibility.
Add-Once `
    -Target (Join-Path $root "AFIP_PROJECT_DATABASE.md") `
    -AppendFile $dbAppend `
    -Marker "Milestone S Pack 6.2"

Add-Once `
    -Target (Join-Path $root "HANDOFF.md") `
    -AppendFile $handoffAppend `
    -Marker "Milestone S Pack 6.2 Handoff"

Write-Host "Pack 6.2 documentation updates complete."
