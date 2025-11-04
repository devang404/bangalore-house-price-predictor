# Start the Flask app using the project's virtualenv
# Run this from the project root: PowerShell -> .\start.ps1
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
    Write-Error ".venv not found. Create it with: python -m venv .venv and install requirements: .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}
Write-Host "Starting app with: $venvPython" -ForegroundColor Green
& $venvPython .\app.py
