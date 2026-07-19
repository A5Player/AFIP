$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Test-MarkerPresent {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    $resolvedPath = (Resolve-Path -LiteralPath $Path).Path
    $reader = [System.IO.File]::OpenText($resolvedPath)
    try {
        while (($line = $reader.ReadLine()) -ne $null) {
            if ($line.IndexOf($Marker, [System.StringComparison]::Ordinal) -ge 0) {
                return $true
            }
        }
        return $false
    }
    finally {
        $reader.Dispose()
    }
}

function Append-Once {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Missing append source: $Source"
    }
    if (-not (Test-Path -LiteralPath $Target -PathType Leaf)) {
        throw "Missing target document: $Target"
    }

    if (Test-MarkerPresent -Path $Target -Marker $Marker) {
        Write-Host "Already applied: $Marker"
        return
    }

    $sourcePath = (Resolve-Path -LiteralPath $Source).Path
    $targetPath = (Resolve-Path -LiteralPath $Target).Path
    $sourceText = [System.IO.File]::ReadAllText($sourcePath)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($targetPath, $true, $utf8NoBom)
    try {
        $writer.WriteLine()
        $writer.Write($sourceText)
        if (-not $sourceText.EndsWith([Environment]::NewLine, [System.StringComparison]::Ordinal)) {
            $writer.WriteLine()
        }
    }
    finally {
        $writer.Dispose()
    }

    Write-Host "Appended $Source to $Target"
}

$projectDatabaseAppend = @{
    Source = "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_3_1_APPEND.md"
    Target = "AFIP_PROJECT_DATABASE.md"
    Marker = "Phase U Pack 3.3.1"
}
Append-Once @projectDatabaseAppend

$handoffAppend = @{
    Source = "HANDOFF_PHASE_U_PACK_3_3_1_APPEND.md"
    Target = "HANDOFF.md"
    Marker = "Phase U Pack 3.3.1 Handoff"
}
Append-Once @handoffAppend

Write-Host "Documentation update completed."
