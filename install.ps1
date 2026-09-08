param(
    [switch]$WithAutostart
)

$ErrorActionPreference = "Stop"
$dir = $PSScriptRoot

Write-Host "=== Tekken 8 Assistant installer ===" -ForegroundColor Yellow

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python not found. Install it from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "(check 'Add python.exe to PATH' during install), then run this script again."
    exit 1
}

Write-Host "[1/4] Installing Python dependencies..."
python -m pip install -r "$dir\requirements.txt" --quiet --disable-pip-version-check
Write-Host "      done." -ForegroundColor Green

Write-Host "[2/4] Checking Tesseract-OCR..."
$tess = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $tess) { $tess = (Get-Command tesseract -ErrorAction SilentlyContinue).Source }
if ($tess) {
    Write-Host "      found: $tess" -ForegroundColor Green
} else {
    Write-Warning "Tesseract-OCR not found - character detection will not work."
    Write-Host "      Install it from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
}

Write-Host "[3/4] Creating desktop shortcuts..."
$desktop = [Environment]::GetFolderPath('Desktop')
$ws = New-Object -ComObject WScript.Shell
$pyw = $python.Source -replace 'python\.exe$', 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pyw)) { $pyw = $python.Source }
$icon = "$dir\assets\icons\assistant.ico"
$iconStop = "$dir\assets\icons\stop.ico"

$lnk = $ws.CreateShortcut("$desktop\Tekken 8 Assistant.lnk")
$lnk.TargetPath = $pyw
$lnk.Arguments = 'main.py'
$lnk.WorkingDirectory = $dir
$lnk.IconLocation = "$icon,0"
$lnk.Save()

$lnk2 = $ws.CreateShortcut("$desktop\Tekken Assistant Stop.lnk")
$lnk2.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$lnk2.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$dir\stop.ps1`""
$lnk2.WorkingDirectory = $dir
$lnk2.IconLocation = "$iconStop,0"
$lnk2.Save()
Write-Host "      done." -ForegroundColor Green

if ($WithAutostart) {
    Write-Host "[4/4] Setting up autostart with the game..."
    $wdir = "$env:LOCALAPPDATA\TekkenAssistant"
    New-Item -ItemType Directory -Force -Path $wdir | Out-Null
    (Get-Content -LiteralPath "$dir\watcher.ps1" -Raw).Replace('__PROJECT_DIR__', $dir) |
        Set-Content -LiteralPath "$wdir\watcher.ps1" -Encoding utf8BOM
    $startup = [Environment]::GetFolderPath('Startup')
    $lnk3 = $ws.CreateShortcut("$startup\Tekken Assistant Autostart.lnk")
    $lnk3.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $lnk3.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$wdir\watcher.ps1`""
    $lnk3.WorkingDirectory = $wdir
    $lnk3.IconLocation = "$icon,0"
    $lnk3.Save()
    Write-Host "      done. The assistant will start with Tekken 8." -ForegroundColor Green
} else {
    Write-Host "[4/4] Autostart skipped (use -WithAutostart to enable)."
}

Write-Host ""
Write-Host "Install complete! Launch: 'Tekken 8 Assistant' on the desktop." -ForegroundColor Yellow
