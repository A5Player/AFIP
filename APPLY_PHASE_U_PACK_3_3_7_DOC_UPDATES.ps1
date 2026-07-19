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
    if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Missing documentation append source: $Source" }
    if (-not (Test-Path -LiteralPath $targetPath)) { New-Item -ItemType File -Path $targetPath -Force | Out-Null }

    $found = Select-String -LiteralPath $targetPath -SimpleMatch -Pattern $Marker -Quiet
    if ($found) {
        Write-Host "Already applied: $Marker"
        return
    }

    $content = [System.IO.File]::ReadAllText($sourcePath, [System.Text.Encoding]::UTF8)
    [System.IO.File]::AppendAllText($targetPath, $content, [System.Text.Encoding]::UTF8)
    Write-Host "Appended $Source to $Target"
}

$projectDatabaseAppend = @{
    Target = "AFIP_PROJECT_DATABASE.md"
    Source = "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_3_7_APPEND.md"
    Marker = "Phase U Pack 3.3.7"
}
$handoffAppend = @{
    Target = "HANDOFF.md"
    Source = "HANDOFF_PHASE_U_PACK_3_3_7_APPEND.md"
    Marker = "Phase U Pack 3.3.7 Handoff"
}
Append-Once @projectDatabaseAppend
Append-Once @handoffAppend
Write-Host "Documentation update completed."
