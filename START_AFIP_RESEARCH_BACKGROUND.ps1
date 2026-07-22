param([string]$ProjectRoot = "C:\AFIP\source")
$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$control = Join-Path $ProjectRoot "runtime\control"
$logs = Join-Path $ProjectRoot "runtime\logs"
New-Item -ItemType Directory -Force $control,$logs | Out-Null
$pidFile = Join-Path $control "afip_research_background.pid"
$stopFlag = Join-Path $control "stop_phase_v_major.flag"
Remove-Item $stopFlag -ErrorAction SilentlyContinue
if (Test-Path $pidFile) {
  $oldPid = [int](Get-Content $pidFile -ErrorAction SilentlyContinue)
  if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
    Write-Host "AFIP research is already running. PID: $oldPid"; exit 0
  }
  Remove-Item $pidFile -ErrorAction SilentlyContinue
}
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python venv not found: $python" }
$out = Join-Path $logs "afip_research_background.out.log"
$err = Join-Path $logs "afip_research_background.err.log"
$p = Start-Process -FilePath $python -ArgumentList @("-m","tools.afip_phase_v_major","run-forever","--root",$ProjectRoot) -WorkingDirectory $ProjectRoot -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
Set-Content -Path $pidFile -Value $p.Id
Write-Host "AFIP background research started. PID: $($p.Id)"
Write-Host "Trading runtime is independent and is not blocked by this process."
Write-Host "Dashboard evidence: runtime\research\automatic_research_status.json"
