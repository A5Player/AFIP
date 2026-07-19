$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Append-Once {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    $targetPath = Join-Path $Root $Target
    $sourcePath = Join-Path $Root $Source

    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "Missing append source: $Source"
    }

    if (-not (Test-Path -LiteralPath $targetPath)) {
        New-Item -ItemType File -Path $targetPath -Force | Out-Null
    }

    $alreadyApplied = Select-String `
        -LiteralPath $targetPath `
        -SimpleMatch `
        -Pattern $Marker `
        -Quiet `
        -ErrorAction SilentlyContinue

    if ($alreadyApplied) {
        Write-Host "Already applied: $Marker"
        return
    }

    $sourceText = [System.IO.File]::ReadAllText(
        $sourcePath,
        [System.Text.Encoding]::UTF8
    )

    [System.IO.File]::AppendAllText(
        $targetPath,
        $sourceText,
        [System.Text.UTF8Encoding]::new($false)
    )

    Write-Host "Appended $Source to $Target"
}

$projectDatabaseAppend = @{
    Target = 'AFIP_PROJECT_DATABASE.md'
    Source = 'AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_3_6_APPEND.md'
    Marker = 'Phase U Pack 3.3.6'
}
Append-Once @projectDatabaseAppend

$handoffAppend = @{
    Target = 'HANDOFF.md'
    Source = 'HANDOFF_PHASE_U_PACK_3_3_6_APPEND.md'
    Marker = 'Phase U Pack 3.3.6 Handoff'
}
Append-Once @handoffAppend

Write-Host "Documentation update completed."
