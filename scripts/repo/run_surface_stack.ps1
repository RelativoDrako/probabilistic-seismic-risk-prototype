[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [int]$ApiPort = 8000,
    [int]$WebPort = 8501,
    [switch]$StartApi,
    [switch]$StartWeb
)

$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$venvPython = Join-Path $repoRootPath "venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = Join-Path $repoRootPath ".venv\Scripts\python.exe"
}
$pythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }

$apiEntry = Join-Path $repoRootPath "src\api\main.py"
$webEntry = Join-Path $repoRootPath "src\web\app.py"

if (-not (Test-Path -LiteralPath $apiEntry)) {
    throw "Missing API entrypoint: $apiEntry"
}
if (-not (Test-Path -LiteralPath $webEntry)) {
    throw "Missing web entrypoint: $webEntry"
}

$apiCommand = "& `"$pythonExe`" -m uvicorn src.api.main:app --host 127.0.0.1 --port $ApiPort"
$webCommand = "& `"$pythonExe`" -m streamlit run `"$webEntry`" --server.address 127.0.0.1 --server.port $WebPort"

Write-Host "[run_surface_stack] canonical commands:"
Write-Host ("API: {0}" -f $apiCommand)
Write-Host ("WEB: {0}" -f $webCommand)
Write-Host ("API URL: http://127.0.0.1:{0}/docs" -f $ApiPort)
Write-Host ("WEB URL: http://127.0.0.1:{0}" -f $WebPort)

if ($StartApi) {
    Start-Process powershell -ArgumentList @(
        "-ExecutionPolicy", "Bypass",
        "-NoExit",
        "-Command",
        "Set-Location -LiteralPath '$repoRootPath'; $apiCommand"
    ) | Out-Null
    Write-Host "[run_surface_stack] API process started."
}

if ($StartWeb) {
    Start-Process powershell -ArgumentList @(
        "-ExecutionPolicy", "Bypass",
        "-NoExit",
        "-Command",
        "Set-Location -LiteralPath '$repoRootPath'; $webCommand"
    ) | Out-Null
    Write-Host "[run_surface_stack] Web process started."
}
