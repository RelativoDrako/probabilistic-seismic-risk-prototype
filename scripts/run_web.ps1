param(
    [string]$PythonExe = "python",
    [Alias("Host")]
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8501,
    [string]$DbPath
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    if ($DbPath) {
        $env:SEISMIC_DB_PATH = $DbPath
    }
    & $PythonExe -m streamlit run src/web/app.py --server.headless true --server.port $Port --server.address $ListenHost
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
