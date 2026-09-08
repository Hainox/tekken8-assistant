$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $PSScriptRoot

python -m pip install pyinstaller --quiet --disable-pip-version-check
$excludes = @(
    'torch', 'cv2', 'scipy', 'grpc', 'transformers', 'tokenizers',
    'matplotlib', 'pandas', 'IPython', 'notebook', 'hf_xet',
    'huggingface_hub', 'sympy', 'networkx', 'pytz'
) | ForEach-Object { "--exclude-module=$_" }

python -m PyInstaller `
    --onefile `
    --noconsole `
    --name Tekken8Assistant `
    --icon "$dir\assets\icons\assistant.ico" `
    --add-data "$dir\tekken_assistant\data;tekken_assistant\data" `
    @excludes `
    "$dir\main.py"

$exe = "$dir\dist\Tekken8Assistant.exe"
if (Test-Path $exe) {
    Write-Host "OK: $exe ($([math]::Round((Get-Item $exe).Length / 1MB, 1)) MB)"
} else {
    Write-Host "BUILD FAILED"
    exit 1
}
