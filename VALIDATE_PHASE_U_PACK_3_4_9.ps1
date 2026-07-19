$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path ".\.venv\Scripts\python.exe") {
    $Python = ".\.venv\Scripts\python.exe"
} else {
    $Python = "python"
}

function Invoke-PythonChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments,
        [Parameter(Mandatory = $true)]
        [string] $Step
    )

    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "AFIP Phase U Pack 3.4.9 validation failed during '$Step' (Python exit code $LASTEXITCODE)."
    }
}

Invoke-PythonChecked -Step "pack tests" -Arguments @(
    "-m", "pytest", "tests/test_phase_u_pack_3_4_9.py", "-q"
)
Invoke-PythonChecked -Step "full regression" -Arguments @(
    "-m", "pytest", "-q"
)
Invoke-PythonChecked -Step "local quality check" -Arguments @(
    "tools/afip_local_quality_check.py"
)
Invoke-PythonChecked -Step "dashboard generation" -Arguments @(
    "-m", "afip.dashboard_ui"
)

Write-Host "Phase U Pack 3.4.9 validation complete."
