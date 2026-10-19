# Katakuri AI - PowerShell Launcher
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython (Join-Path $ScriptDir "run_app.py")
} else {
    python (Join-Path $ScriptDir "run_app.py")
}
