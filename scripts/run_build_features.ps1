param(
    [Parameter(Mandatory = $true)] [string]$IngestBatchId,
    [Parameter(Mandatory = $true)] [string]$FeatureSetVersion,
    [Parameter(Mandatory = $true)] [string]$WindowSpec,
    [string]$PythonExe = "python"
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Push-Location $ProjectRoot
try {
    & $PythonExe -m src.features.cli `
        --ingest-batch-id $IngestBatchId `
        --feature-set-version $FeatureSetVersion `
        --window-spec $WindowSpec
}
finally {
    Pop-Location
}
