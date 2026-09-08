param(
    [string]$OutDir = "build/tesseract"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root $OutDir

$src = @(
    "C:\Program Files\Tesseract-OCR",
    "C:\Program Files (x86)\Tesseract-OCR"
) | Where-Object { Test-Path (Join-Path $_ "tesseract.exe") } | Select-Object -First 1

if (-not $src) {
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Installing Tesseract via chocolatey..."
        choco install tesseract -y --no-progress
        $src = "C:\Program Files\Tesseract-OCR"
    } else {
        Write-Error "Tesseract-OCR not found and chocolatey is unavailable."
        exit 1
    }
}

if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
New-Item -ItemType Directory -Force -Path "$dest\tessdata" | Out-Null
Copy-Item "$src\tesseract.exe" $dest
# OpenSSL DLLs are only needed by tesseract training tools, not for OCR
Get-ChildItem "$src\*.dll" |
    Where-Object { $_.Name -notmatch '^lib(ssl|crypto)-' } |
    Copy-Item -Destination $dest
Copy-Item "$src\tessdata\eng.traineddata" "$dest\tessdata"
# osd.traineddata (~10 MB) is not needed: the app uses fixed psm modes (6/11)

$size = [math]::Round((Get-ChildItem $dest -Recurse | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host "Tesseract prepared: $dest ($size MB)"
