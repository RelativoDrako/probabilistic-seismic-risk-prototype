param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PatchRoot = Join-Path $ScriptRoot "..\repo_patch"
$TargetRel = "src\ingestion\manifest_service.py"
$Target = Join-Path $RepoRoot $TargetRel

if (!(Test-Path $Target)) {
    throw "No existe archivo objetivo: $Target"
}

$BackupRoot = Join-Path $RepoRoot "_ops_backups\ingestion_manifest_service_definitive_fix"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $BackupRoot $Timestamp
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$BackupFile = Join-Path $BackupDir "manifest_service.py"
Copy-Item $Target $BackupFile -Force

$PatchFile = Join-Path $PatchRoot $TargetRel
if (!(Test-Path $PatchFile)) {
    throw "No existe archivo patch: $PatchFile"
}

Copy-Item $PatchFile $Target -Force

Write-Host "[ok] backup_file=$BackupFile"
Write-Host "[ok] patched=$Target"
Write-Host "[next] rerun ingest for usgs_mexico_catalog"
