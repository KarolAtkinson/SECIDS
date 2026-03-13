# SecIDS-CNN public WebUI launcher for Windows PowerShell
# Binds WebUI and prints shareable URLs for local/LAN/public access.

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

$HostAddr = if ($env:SECIDS_WEB_HOST) { $env:SECIDS_WEB_HOST } else { "0.0.0.0" }
$Port = if ($env:SECIDS_WEB_PORT) { $env:SECIDS_WEB_PORT } else { "8080" }
$SessionTimeout = if ($env:SECIDS_SESSION_TIMEOUT_SECONDS) { $env:SECIDS_SESSION_TIMEOUT_SECONDS } else { "86400" }

$LoginPath = (& $VenvPython -c "from WebUI.app import create_app; app=create_app(); print(app.config.get('SECIDS_LOGIN_PATH','/login'))").Trim()
$AccessPath = (& $VenvPython -c "from WebUI.app import create_app; app=create_app(); print(app.config.get('SECIDS_ACCESS_PATH',''))").Trim()

$LocalLogin = "http://127.0.0.1`:$Port$LoginPath"
$LocalWebUi = "http://127.0.0.1`:$Port$AccessPath"

$LanIp = ""
try {
    $LanIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "169.254.*" -and $_.IPAddress -ne "127.0.0.1" } | Select-Object -First 1 -ExpandProperty IPAddress)
} catch {}

$PublicIp = ""
try {
    $PublicIp = (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 5)
} catch {}

Write-Host "[webui-public.ps1] Session timeout: ${SessionTimeout}s"
Write-Host "[webui-public.ps1] Login path: $LoginPath"
Write-Host "[webui-public.ps1] Local login URL: $LocalLogin"
Write-Host "[webui-public.ps1] Local WebUI URL: $LocalWebUi"
if ($LanIp) {
    Write-Host "[webui-public.ps1] LAN login URL: http://$LanIp`:$Port$LoginPath"
    Write-Host "[webui-public.ps1] LAN WebUI URL:  http://$LanIp`:$Port$AccessPath"
}
if ($PublicIp) {
    Write-Host "[webui-public.ps1] Public login URL: http://$PublicIp`:$Port$LoginPath"
    Write-Host "[webui-public.ps1] Public WebUI URL:  http://$PublicIp`:$Port$AccessPath"
    Write-Host "[webui-public.ps1] Note: Public URL requires router/NAT forwarding TCP $Port -> this host"
}

$Listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq [int]$Port }
if ($Listening) {
    Write-Host "[webui-public.ps1] Port $Port already in use; reusing existing listener"
    exit 0
}

$env:SECIDS_WEB_HOST = $HostAddr
$env:SECIDS_WEB_PORT = "$Port"
$env:SECIDS_WEB_OPEN_BROWSER = "0"
$env:SECIDS_SESSION_TIMEOUT_SECONDS = "$SessionTimeout"

Write-Host "[webui-public.ps1] Starting production WebUI on ${HostAddr}:$Port"
& $VenvPython "WebUI/production_server.py"
