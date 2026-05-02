param(
    [Parameter(Mandatory = $true)] [string]$SourceId,
    [Parameter(Mandatory = $true)] [string]$IngestBatchId,
    [Parameter(Mandatory = $true)] [string]$CurationVersion,
    [string]$PythonExe = "python"
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Push-Location $ProjectRoot
try {
    & $PythonExe -m src.processing.cli `
        --source-id $SourceId `
        --ingest-batch-id $IngestBatchId `
        --curation-version $CurationVersion
}
finally {
    Pop-Location
}
