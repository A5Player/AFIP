param([string]$ProjectRoot="C:\AFIP")
$ErrorActionPreference="Stop"
Set-Location $ProjectRoot

$targets=@(
"tools\afip_verify_account_isolation.py",
"afip\demo_execution_gateway\runtime.py"
)

$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$backup=Join-Path $ProjectRoot "runtime\installation_backups\mt5_existing_session_ipc_fix_$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null
$changed=0

foreach($relative in $targets){
  $path=Join-Path $ProjectRoot $relative
  if(-not(Test-Path $path)){throw "Missing source file: $path"}

  $backupPath=Join-Path $backup $relative
  New-Item -ItemType Directory -Path (Split-Path $backupPath -Parent) -Force | Out-Null
  Copy-Item $path $backupPath -Force

  $original=[IO.File]::ReadAllText($path)
  $updated=$original
  $updated=[regex]::Replace($updated,'(?m)^[ \t]*portable[ \t]*=[ \t]*True[ \t]*,[ \t]*\r?\n','')
  $updated=[regex]::Replace($updated,',[ \t]*portable[ \t]*=[ \t]*True','')
  $updated=[regex]::Replace($updated,'portable[ \t]*=[ \t]*True[ \t]*,','')

  if($updated -ne $original){
    [IO.File]::WriteAllText($path,$updated,[Text.UTF8Encoding]::new($false))
    Write-Host "Patched: $relative"
    $changed++
  } else {
    Write-Host "No portable=True found: $relative"
  }
}

if($changed -eq 0){throw "No source changes were made."}

$python=Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if(-not(Test-Path $python)){throw "Missing venv Python: $python"}

& $python -m py_compile `
  (Join-Path $ProjectRoot "tools\afip_verify_account_isolation.py") `
  (Join-Path $ProjectRoot "afip\demo_execution_gateway\runtime.py")
if($LASTEXITCODE -ne 0){throw "Python syntax validation failed."}

$remaining=Select-String -Path `
  (Join-Path $ProjectRoot "tools\afip_verify_account_isolation.py"),`
  (Join-Path $ProjectRoot "afip\demo_execution_gateway\runtime.py") `
  -Pattern 'portable\s*=\s*True' -ErrorAction SilentlyContinue
if($remaining){throw "portable=True still remains in a runtime authority."}

Write-Host ""
Write-Host "AFIP V1 MT5 Existing Session IPC Fix: INSTALLED"
Write-Host "Backup: $backup"
