param(
    [Parameter(Mandatory = $true)] [string]$IngestBatchId,
    [Parameter(Mandatory = $true)] [string]$FeatureSetVersion,
    [string]$OutputDir,
    [string]$PythonExe = "python"
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Push-Location $ProjectRoot
try {
    $Args = @(
        "-m", "src.visualization.cli",
        "--ingest-batch-id", $IngestBatchId,
        "--feature-set-version", $FeatureSetVersion
    )
    if ($OutputDir) {
        $Args += @("--output-dir", $OutputDir)
    }
    & $PythonExe @Args
}
finally {
    Pop-Location
}
