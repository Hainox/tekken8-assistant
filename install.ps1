param(
    [switch]$WithAutostart
)

$ErrorActionPreference = "Stop"
$dir = $PSScriptRoot

Write-Host "=== Установка Tekken 8 Assistant ===" -ForegroundColor Yellow

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python не найден. Установите его с https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "(при установке отметьте 'Add python.exe to PATH') и запустите скрипт снова."
    exit 1
}

Write-Host "[1/4] Установка Python-зависимостей..."
python -m pip install -r "$dir\requirements.txt" --quiet --disable-pip-version-check
Write-Host "      готово." -ForegroundColor Green

Write-Host "[2/4] Проверка Tesseract-OCR..."
$tess = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $tess) { $tess = (Get-Command tesseract -ErrorAction SilentlyContinue).Source }
if ($tess) {
    Write-Host "      найден: $tess" -ForegroundColor Green
} else {
    Write-Host "      Tesseract-OCR не найден, пробую установить через winget..." -ForegroundColor Yellow
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        winget install --id UB-Mannheim.TesseractOCR -e --silent --accept-source-agreements --accept-package-agreements
        $tess = @("C:\Program Files\Tesseract-OCR\tesseract.exe") | Where-Object { Test-Path -LiteralPath $_ }
        if ($tess) { Write-Host "      Tesseract установлен." -ForegroundColor Green }
        else { Write-Warning "Не удалось установить Tesseract автоматически. Установите вручную: https://github.com/UB-Mannheim/tesseract/wiki" }
    } else {
        Write-Warning "winget не найден. Установите Tesseract вручную: https://github.com/UB-Mannheim/tesseract/wiki"
    }
}

Write-Host "[3/4] Создание ярлыков на рабочем столе..."
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

$lnk2 = $ws.CreateShortcut("$desktop\Tekken Assistant Стоп.lnk")
$lnk2.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$lnk2.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$dir\stop.ps1`""
$lnk2.WorkingDirectory = $dir
$lnk2.IconLocation = "$iconStop,0"
$lnk2.Save()
Write-Host "      готово." -ForegroundColor Green

if ($WithAutostart) {
    Write-Host "[4/4] Настройка автозапуска вместе с игрой..."
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
    Write-Host "      готово. Ассистент будет запускаться вместе с Tekken 8." -ForegroundColor Green
} else {
    Write-Host "[4/4] Автозапуск пропущен (добавьте ключ -WithAutostart, чтобы включить)."
}

Write-Host ""
Write-Host "Установка завершена! Запуск: ярлык 'Tekken 8 Assistant' на рабочем столе." -ForegroundColor Yellow
