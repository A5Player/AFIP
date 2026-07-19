$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Append-Once {
    param(
        [Parameter(Mandatory=$true)][string]$Target,
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Marker
    )
    $targetPath = Join-Path $Root $Target
    $sourcePath = Join-Path $Root $Source
    if (-not (Test-Path $sourcePath)) { throw "Missing append source: $Source" }
    if (-not (Test-Path $targetPath)) { New-Item -ItemType File -Path $targetPath -Force | Out-Null }
    $found = Select-String -Path $targetPath -SimpleMatch -Pattern $Marker -Quiet -ErrorAction SilentlyContinue
    if ($found) { Write-Host "Already applied: $Marker"; return }
    [System.IO.File]::AppendAllText($targetPath, [System.IO.File]::ReadAllText($sourcePath, [System.Text.Encoding]::UTF8), [System.Text.UTF8Encoding]::new($false))
    Write-Host "Appended $Source to $Target"
}

$dbArgs = @{ Target='AFIP_PROJECT_DATABASE.md'; Source='AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_3_4_APPEND.md'; Marker='Phase U Pack 3.3.4' }
$handoffArgs = @{ Target='HANDOFF.md'; Source='HANDOFF_PHASE_U_PACK_3_3_4_APPEND.md'; Marker='Phase U Pack 3.3.4 Handoff' }
Append-Once @dbArgs
Append-Once @handoffArgs
Write-Host "Documentation update completed."
