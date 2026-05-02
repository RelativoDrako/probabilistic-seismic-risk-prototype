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

function Resolve-SourceName {
    param([string]$Id)
    if ($Id -eq "ssn") { return "Servicio Sismologico Nacional" }
    return $Id
}

if (-not (Test-Path -LiteralPath $RawInputDir -PathType Container)) {
    Write-Error "RawInputDir not found: $RawInputDir"
    exit 1
}

$rawFiles = @(Get-ChildItem -LiteralPath $RawInputDir -Recurse -File | Sort-Object FullName | Select-Object -ExpandProperty FullName)
if ($rawFiles.Count -eq 0) {
    Write-Error "No raw files found under RawInputDir: $RawInputDir"
    exit 1
}

$sourceName = Resolve-SourceName -Id $SourceId
$ingestArgs = @{
    SourceId = $SourceId
    SourceName = $sourceName
    RawFile = $rawFiles
}
if ($DbPath) { $ingestArgs["DbPath"] = $DbPath }
if ($BatchLabel) { $ingestArgs["Notes"] = $BatchLabel }

$ingestOutput = & "$PSScriptRoot\run_ingest.ps1" @ingestArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$ingestPayload = ($ingestOutput | Out-String) | ConvertFrom-Json
$ingestBatchId = $ingestPayload.batch.batch_id
if ([string]::IsNullOrWhiteSpace($ingestBatchId)) {
    Write-Error "Unable to resolve ingest batch id from run_ingest.ps1 output."
    exit 1
}

$curateArgs = @{
    SourceId = $SourceId
    SourceName = $sourceName
    BatchId = $ingestBatchId
    RawFile = $rawFiles
}
if ($DbPath) { $curateArgs["DbPath"] = $DbPath }

& "$PSScriptRoot\run_curate.ps1" @curateArgs | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$featureArgs = @{
    SourceBatchScope = $ingestBatchId
    FeatureSetVersion = $FeatureSetVersion
    WindowSpec = $WindowSpec
    PythonExe = $PythonExe
}
if ($DbPath) { $featureArgs["DbPath"] = $DbPath }

$featureGenerationId = (& "$PSScriptRoot\run_build_features.ps1" @featureArgs | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ([string]::IsNullOrWhiteSpace($featureGenerationId)) {
    Write-Error "run_build_features.ps1 did not emit a feature_generation_id."
    exit 1
}

Write-Output $featureGenerationId
exit 0
