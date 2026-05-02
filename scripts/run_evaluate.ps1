param(
    [Parameter(Mandatory = $true)]
    [string]$ModelRunId,

    [string]$PythonExe = "python",
    [string]$DbPath
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ModelRunId)) {
    Write-Error "ModelRunId is required."
    exit 1
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    "-m", "src.evaluation.cli",
    "--model-run-id", $ModelRunId
)
if ($DbPath) {
    $arguments += @("--db-path", $DbPath)
}

Push-Location $repoRoot
try {
    & $PythonExe @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
