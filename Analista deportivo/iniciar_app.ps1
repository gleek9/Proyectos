# Katakuri v4.0 - PowerShell Launcher
$Host.UI.RawUI.WindowTitle = "Katakuri v4.0 - Plataforma de Prediccion Deportiva de Alta Precision"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "     INICIANDO KATAKURI v4.0 (ALTA PRECISION & DATOS REALES)" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython (Join-Path $ScriptDir "run_app.py")
} else {
    python (Join-Path $ScriptDir "run_app.py")
}
