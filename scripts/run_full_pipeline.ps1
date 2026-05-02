param(
    [Parameter(Mandatory = $true)]
    [string]$SourceId,

    [Parameter(Mandatory = $true)]
    [string]$BatchLabel,

    [Parameter(Mandatory = $true)]
    [string]$RawInputDir,

    [string]$IngestMode,
    [string]$CurationVersion,
    [string]$FeatureSetVersion = "v1",
    [string]$WindowSpec = "30d",
    [string]$PythonExe = "python",
    [string]$DbPath
)

$ErrorActionPreference = "Stop"

$prepareArgs = @{
    SourceId = $SourceId
    BatchLabel = $BatchLabel
    RawInputDir = $RawInputDir
    FeatureSetVersion = $FeatureSetVersion
    WindowSpec = $WindowSpec
    PythonExe = $PythonExe
}
if ($IngestMode) { $prepareArgs["IngestMode"] = $IngestMode }
if ($CurationVersion) { $prepareArgs["CurationVersion"] = $CurationVersion }
if ($DbPath) { $prepareArgs["DbPath"] = $DbPath }

$featureGenerationId = (& "$PSScriptRoot\run_prepare_dataset.ps1" @prepareArgs | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ([string]::IsNullOrWhiteSpace($featureGenerationId)) {
    Write-Error "run_prepare_dataset.ps1 did not emit a feature_generation_id."
    exit 1
}

$trainArgs = @{
    FeatureGenerationId = $featureGenerationId
    PythonExe = $PythonExe
}
if ($DbPath) { $trainArgs["DbPath"] = $DbPath }

$modelRunId = (& "$PSScriptRoot\run_train.ps1" @trainArgs | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ([string]::IsNullOrWhiteSpace($modelRunId)) {
    Write-Error "run_train.ps1 did not emit a model_run_id."
    exit 1
}

$evaluateArgs = @{
    ModelRunId = $modelRunId
    PythonExe = $PythonExe
}
if ($DbPath) { $evaluateArgs["DbPath"] = $DbPath }

$evaluationReportId = (& "$PSScriptRoot\run_evaluate.ps1" @evaluateArgs | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ([string]::IsNullOrWhiteSpace($evaluationReportId)) {
    Write-Error "run_evaluate.ps1 did not emit an evaluation_report_id."
    exit 1
}

Write-Output $evaluationReportId
exit 0
