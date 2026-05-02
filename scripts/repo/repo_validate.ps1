[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-CanonicalPath {
    param([string]$Path)
    $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
    return $resolved.Path
}

function Test-RequiredPath {
    param(
        [string]$Base,
        [string]$Relative,
        [string]$Type
    )
    $target = Join-Path $Base $Relative
    $exists = Test-Path -LiteralPath $target
    if (-not $exists) {
        return [pscustomobject]@{ Relative = $Relative; Type = $Type; Exists = $false }
    }

    $item = Get-Item -LiteralPath $target -Force
    $typeMatches = (($Type -eq 'Directory' -and $item.PSIsContainer) -or ($Type -eq 'File' -and -not $item.PSIsContainer))
    return [pscustomobject]@{ Relative = $Relative; Type = $Type; Exists = $typeMatches }
}

$repoRootPath = Resolve-CanonicalPath -Path $RepoRoot
$reportsDir = Join-Path $repoRootPath 'artifacts/reports'
[void](New-Item -ItemType Directory -Path $reportsDir -Force)
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$jsonReportPath = Join-Path $reportsDir ("repo_validation_report_{0}.json" -f $timestamp)
$mdReportPath = Join-Path $reportsDir ("repo_validation_report_{0}.md" -f $timestamp)

$errors = @()
$warnings = @()
$checks = @()

$requiredPaths = @(
    @{ Relative = 'README.md'; Type = 'File' },
    @{ Relative = 'DISCLAIMER.md'; Type = 'File' },
    @{ Relative = 'HOW_TO_RUN.md'; Type = 'File' },
    @{ Relative = 'roadmap.md'; Type = 'File' },
    @{ Relative = 'docs/architecture.md'; Type = 'File' },
    @{ Relative = 'docs/data_governance.md'; Type = 'File' },
    @{ Relative = 'docs/model_card.md'; Type = 'File' },
    @{ Relative = 'docs/adr/ADR-001-scope-and-positioning.md'; Type = 'File' },
    @{ Relative = 'docs/adr/ADR-002-data-authority-sqlite.md'; Type = 'File' },
    @{ Relative = 'docs/adr/ADR-003-open-source-local-first.md'; Type = 'File' },
    @{ Relative = 'src/api'; Type = 'Directory' },
    @{ Relative = 'src/web'; Type = 'Directory' },
    @{ Relative = 'artifacts/sqlite'; Type = 'Directory' },
    @{ Relative = 'presentations'; Type = 'Directory' }
)

foreach ($required in $requiredPaths) {
    $result = Test-RequiredPath -Base $repoRootPath -Relative $required.Relative -Type $required.Type
    $checks += $result
    if (-not $result.Exists) {
        $errors += ("Missing required {0}: {1}" -f $required.Type.ToLowerInvariant(), $required.Relative)
    }
}

$forbiddenNamedPaths = @(
    '_ops_backup',
    '_ops_backups',
    '_ops_logs',
    '_ops_staging',
    'tmp',
    'tmp_outputs',
    'old_reports',
    'old_plots',
    'backup_scripts',
    'draft_notes'
)

foreach ($relativePath in $forbiddenNamedPaths) {
    $fullPath = Join-Path $repoRootPath $relativePath
    if (Test-Path -LiteralPath $fullPath) {
        $errors += ("Forbidden residue still present: {0}" -f $relativePath)
    }
}

$duplicateCopies = Get-ChildItem -LiteralPath $repoRootPath -Recurse -File -Force | Where-Object {
    $_.Name -match ' \([0-9]+\)(?=\.[^.]+$|$)'
}
foreach ($dup in $duplicateCopies) {
    $errors += ("Duplicate copy naming still present: {0}" -f $dup.FullName)
}

$pyCaches = Get-ChildItem -LiteralPath $repoRootPath -Recurse -Directory -Force | Where-Object {
    $_.Name -eq '__pycache__'
}
foreach ($cache in $pyCaches) {
    $errors += ("Python cache directory still present: {0}" -f $cache.FullName)
}

# Large committed payloads warning only; raw evidence may be intentional in this prototype.
$dataPath = Join-Path $repoRootPath 'data'
if (Test-Path -LiteralPath $dataPath) {
    Get-ChildItem -LiteralPath $dataPath -Recurse -File -Force | Where-Object { $_.Length -ge 10MB } | ForEach-Object {
        $warnings += ("Large data file detected: {0} ({1} MB)" -f $_.FullName, [math]::Round($_.Length / 1MB, 2))
    }
}

$rootPatchDocs = Get-ChildItem -LiteralPath $repoRootPath -File -Force | Where-Object {
    $_.Name -match '^(README_.*|INSTRUCCIONES_.*|PHASE.*|README_PHASE.*)$'
}
foreach ($doc in $rootPatchDocs) {
    $warnings += ("Root patch-era document still present: {0}" -f $doc.Name)
}

$status = if (@($errors).Count -eq 0) { 'PASS' } else { 'FAIL' }

$summary = [pscustomobject]@{
    RepoRoot       = $repoRootPath
    TimestampUtc   = (Get-Date).ToUniversalTime().ToString('o')
    Status         = $status
    ErrorCount     = @($errors).Count
    WarningCount   = @($warnings).Count
    Checks         = @($checks)
    Errors         = @($errors)
    Warnings       = @($warnings)
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonReportPath -Encoding UTF8

$md = @"
# Repository validation report

- repo_root: `$repoRootPath`
- timestamp_utc: `$(Get-Date).ToUniversalTime().ToString('o')`
- status: **$status**
- errors: $(@($errors).Count)
- warnings: $(@($warnings).Count)

## Errors
$(if (@($errors).Count -gt 0) { ((@($errors) | ForEach-Object { "- $_" }) -join [Environment]::NewLine) } else { '- none' })

## Warnings
$(if (@($warnings).Count -gt 0) { ((@($warnings) | ForEach-Object { "- $_" }) -join [Environment]::NewLine) } else { '- none' })
"@

$md | Set-Content -LiteralPath $mdReportPath -Encoding UTF8

Write-Host "[repo_validate] status=$status errors=$(@($errors).Count) warnings=$(@($warnings).Count)"
Write-Host "[repo_validate] json=$jsonReportPath"
Write-Host "[repo_validate] markdown=$mdReportPath"

if ($status -ne 'PASS') {
    exit 1
}
