param(
    [Parameter(Mandatory = $true)] [string]$SourceId,
    [Parameter(Mandatory = $true)] [string]$SourceName,
    [Parameter(Mandatory = $true)] [string]$SourceKind,
    [Parameter(Mandatory = $true)] [string]$Provider,
    [Parameter(Mandatory = $true)] [string]$RawInputDir,
    [Parameter(Mandatory = $true)] [string]$BatchLabel,
    [Parameter(Mandatory = $true)] [string]$IngestMode,
    [string]$SourceUrl,
    [string]$LicenseNote,
    [string]$SourceSnapshotRef,
    [string]$CountryScope = "MX",
    [string]$PythonExe = "python"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")

Push-Location $ProjectRoot
try {
    & $PythonExe -m src.ingestion.cli `
        --source-id $SourceId `
        --source-name $SourceName `
        --source-kind $SourceKind `
        --provider $Provider `
        --raw-input-dir $RawInputDir `
        --batch-label $BatchLabel `
        --ingest-mode $IngestMode `
        --country-scope $CountryScope `
        @(
            if ($SourceUrl) { "--source-url"; $SourceUrl }
            if ($LicenseNote) { "--license-note"; $LicenseNote }
            if ($SourceSnapshotRef) { "--source-snapshot-ref"; $SourceSnapshotRef }
        )
}
finally {
    Pop-Location
}
