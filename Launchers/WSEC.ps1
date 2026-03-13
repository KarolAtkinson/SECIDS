# SecIDS-CNN WebUI launcher (WSEC) for Windows PowerShell
# Starts production WebUI (if not running) and opens WebUI root/login URL.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv_test\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Missing Python environment: $VenvPython" -ForegroundColor Red
    Write-Host "Run: py -3 -m venv .venv_test ; .venv_test\\Scripts\\pip install -r requirements.txt"
    exit 1
}

$HostAddr = if ($env:SECIDS_WEB_HOST) { $env:SECIDS_WEB_HOST } else { "127.0.0.1" }
$Port = if ($env:SECIDS_WEB_PORT) { $env:SECIDS_WEB_PORT } else { "8080" }

$AppPaths = & $VenvPython -c "from WebUI.app import create_app; app=create_app(); print(app.config.get('SECIDS_ACCESS_PATH','')); print(app.config.get('SECIDS_LOGIN_PATH','/login'))"
$AccessPath = ($AppPaths | Select-Object -First 1).Trim()
$LoginPath = ($AppPaths | Select-Object -Last 1).Trim()

$WebUiUrl = "http://$HostAddr`:$Port$AccessPath"
$LoginUrl = "http://$HostAddr`:$Port$LoginPath"

$Existing = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*WebUI/production_server.py*" }
if (-not $Existing) {
    Write-Host "[WSEC.ps1] starting WebUI production server..."
    Start-Process -FilePath $VenvPython -ArgumentList "WebUI/production_server.py" -WorkingDirectory $ProjectRoot -WindowStyle Hidden
    Start-Sleep -Milliseconds 1800
}

$TargetUrl = $WebUiUrl
try {
    $resp = Invoke-WebRequest -Uri $WebUiUrl -Method Get -MaximumRedirection 0 -ErrorAction SilentlyContinue
    if (-not $resp.StatusCode) {
        $TargetUrl = $LoginUrl
    }
} catch {
    $TargetUrl = $LoginUrl
}

Write-Host "[WSEC.ps1] opening: $TargetUrl"
Start-Process $TargetUrl
Write-Host "[WSEC.ps1] ready"
