param(
    [Parameter(Mandatory = $true)]
    [string]$FeatureGenerationId,

    [string]$PythonExe = "python",
    [string]$DbPath
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($FeatureGenerationId)) {
    Write-Error "FeatureGenerationId is required."
    exit 1
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    "-m", "src.training.cli",
    "--feature-generation-id", $FeatureGenerationId
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
