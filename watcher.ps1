# Tekken 8 Assistant watcher.
# Starts the assistant when the game launches, stops it after the game exits.
# install.ps1 replaces __PROJECT_DIR__ with the real project path.

$dir = "__PROJECT_DIR__"
if (-not (Test-Path -LiteralPath $dir)) { $dir = $PSScriptRoot }

$py = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $py) {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source -replace 'python\.exe$', 'pythonw.exe'
}
if (-not $py -or -not (Test-Path -LiteralPath $py)) { exit 1 }

$started = $false

function Get-Assistant {
    Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'main\.py' }
}

while ($true) {
    $game = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'Tekken*' }
    if ($game) {
        if (-not (Get-Assistant)) {
            Start-Process -FilePath $py -ArgumentList 'main.py' -WorkingDirectory $dir
            $started = $true
        }
        Start-Sleep -Seconds 30
    } elseif ($started) {
        Get-Assistant | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        $started = $false
        Start-Sleep -Seconds 5
    } else {
        Start-Sleep -Seconds 5
    }
}
