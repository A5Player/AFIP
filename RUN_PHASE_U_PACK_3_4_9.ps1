$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "AFIP Phase U Pack 3.4.9 - Financial Data Integrity & Intelligence Runtime Certification"
Write-Host "Real-source only. Research only. No execution authority."

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
        throw "AFIP Phase U Pack 3.4.9 failed during '$Step' (Python exit code $LASTEXITCODE)."
    }
}

Invoke-PythonChecked -Step "pack tests" -Arguments @(
    "-m", "pytest", "tests/test_phase_u_pack_3_4_9.py", "-q"
)
Invoke-PythonChecked -Step "runtime certification and research collection" -Arguments @(
    "tools/afip_phase_u_pack_3_4_9_runtime.py", "--root", "."
)
Invoke-PythonChecked -Step "dashboard generation" -Arguments @(
    "-m", "afip.dashboard_ui"
)

Write-Host "Generated runtime certification, cross-market research, and dashboards."
Write-Host "Open runtime\dashboard\afip_dashboard.html"
