param(
    [Parameter(Mandatory = $true)] [string]$IngestBatchId,
    [Parameter(Mandatory = $true)] [string]$FeatureSetVersion,
    [string]$PythonExe = "python"
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Push-Location $ProjectRoot
try {
    & $PythonExe -m src.features.cli --ingest-batch-id $IngestBatchId --feature-set-version $FeatureSetVersion --window-spec 30d
    & $PythonExe -m src.training.cli --ingest-batch-id $IngestBatchId --feature-set-version $FeatureSetVersion
    & $PythonExe -m src.evaluation.cli --ingest-batch-id $IngestBatchId --feature-set-version $FeatureSetVersion
    & $PythonExe -m src.visualization.cli --ingest-batch-id $IngestBatchId --feature-set-version $FeatureSetVersion
}
finally {
    Pop-Location
}
