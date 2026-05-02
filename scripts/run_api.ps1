param(
    [string]$PythonExe = "python",
    [Alias("Host")]
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8000,
    [string]$DbPath
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    if ($DbPath) {
        $env:SEISMIC_DB_PATH = $DbPath
    }
    & $PythonExe -m uvicorn src.api.main:app --host $ListenHost --port $Port
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
