$ErrorActionPreference = "Stop"

function Append-Once {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    $sourceText = Get-Content -Raw -Encoding UTF8 -Path $Source
    $targetText = if (Test-Path -Path $Target) {
        Get-Content -Raw -Encoding UTF8 -Path $Target
    } else {
        ""
    }

    if ($targetText -notmatch [regex]::Escape($Marker)) {
        Add-Content -Path $Target -Value $sourceText -Encoding UTF8
        Write-Host "Appended $Source to $Target"
    } else {
        Write-Host "Already applied: $Marker"
    }
}

Append-Once `
    -Target "AFIP_PROJECT_DATABASE.md" `
    -Source "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_3_10_APPEND.md" `
    -Marker "Phase U Pack 3.3.10"

Append-Once `
    -Target "HANDOFF.md" `
    -Source "HANDOFF_PHASE_U_PACK_3_3_10_APPEND.md" `
    -Marker "Phase U Pack 3.3.10"
