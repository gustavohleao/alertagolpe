$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$portablePython = Join-Path $PSScriptRoot '.tools\python\python.exe'
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $portablePython) {
    & $portablePython -m streamlit run (Join-Path $PSScriptRoot 'app.py')
} elseif (Test-Path -LiteralPath $venvPython) {
    & $venvPython -m streamlit run (Join-Path $PSScriptRoot 'app.py')
} else {
    Write-Error 'Prepare o Python e instale requirements.txt conforme o README.'
}
