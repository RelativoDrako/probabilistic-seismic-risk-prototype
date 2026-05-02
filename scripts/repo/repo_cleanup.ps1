[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = ".",

    [Parameter(Mandatory = $false)]
    [switch]$Apply,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-CanonicalPath {
    param([string]$Path)
    $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
    return $resolved.Path
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        [void](New-Item -ItemType Directory -Path $Path -Force)
    }
}

function New-MarkdownList {
    param([object[]]$Items)
    if (-not $Items -or $Items.Count -eq 0) {
        return "- none"
    }
    return ($Items | ForEach-Object { "- $_" }) -join [Environment]::NewLine
}

function Add-SafeTarget {
    param(
        [string]$CandidatePath,
        [string]$Reason,
        [ref]$Targets
    )

    if (Test-Path -LiteralPath $CandidatePath) {
        $item = Get-Item -LiteralPath $CandidatePath -Force
        $Targets.Value += [pscustomobject]@{
            Path   = $item.FullName
            Type   = if ($item.PSIsContainer) { 'Directory' } else { 'File' }
            Reason = $Reason
        }
    }
}

if (-not $Apply -and -not $DryRun) {
    $DryRun = $true
}

$repoRootPath = Resolve-CanonicalPath -Path $RepoRoot
$reportsDir = Join-Path $repoRootPath 'artifacts/reports'
Ensure-Directory -Path $reportsDir

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$mode = if ($Apply) { 'apply' } else { 'dryrun' }
$jsonReportPath = Join-Path $reportsDir ("repo_cleanup_report_{0}_{1}.json" -f $mode, $timestamp)
$mdReportPath = Join-Path $reportsDir ("repo_cleanup_report_{0}_{1}.md" -f $mode, $timestamp)

$safeTargets = @()
$manualReview = @()
$removed = @()
$errors = @()

# Safe removals: operational residue and generated noise.
$namedPaths = @(
    '_ops_backup',
    '_ops_backups',
    '_ops_logs',
    '_ops_staging',
    'tmp',
    'tmp_outputs',
    'old_reports',
    'old_plots',
    'backup_scripts',
    'draft_notes',
    'repo_patch'
)

foreach ($relativePath in $namedPaths) {
    Add-SafeTarget -CandidatePath (Join-Path $repoRootPath $relativePath) -Reason 'Non-canonical operational residue.' -Targets ([ref]$safeTargets)
}

# Root-level scratch files that clearly violate the current repository tone.
$rootScratchFiles = @(
    'Nuevo Documento de texto.txt',
    '_ops_logspply_migration_tmp.py',
    'scratch.md',
    'executive_summary (1).md'
)

foreach ($relativePath in $rootScratchFiles) {
    Add-SafeTarget -CandidatePath (Join-Path $repoRootPath $relativePath) -Reason 'Scratch or duplicate root file.' -Targets ([ref]$safeTargets)
}

# Duplicate copies like "file (2).ext".
Get-ChildItem -LiteralPath $repoRootPath -Recurse -File -Force | Where-Object {
    $_.Name -match ' \([0-9]+\)(?=\.[^.]+$|$)'
} | ForEach-Object {
    $safeTargets += [pscustomobject]@{
        Path   = $_.FullName
        Type   = 'File'
        Reason = 'Duplicate copy naming pattern.'
    }
}

# Python cache residue.
Get-ChildItem -LiteralPath $repoRootPath -Directory -Recurse -Force | Where-Object {
    $_.Name -eq '__pycache__'
} | ForEach-Object {
    $safeTargets += [pscustomobject]@{
        Path   = $_.FullName
        Type   = 'Directory'
        Reason = 'Python cache directory.'
    }
}

# Competing top-level authorities that should not be removed blindly.
$competingAuthorities = @(
    @{ Legacy = 'architecture'; Canonical = 'docs/architecture'; Reason = 'Competes with canonical documentation tree.' },
    @{ Legacy = 'decisions'; Canonical = 'docs/adr'; Reason = 'Potential ADR consolidation required.' },
    @{ Legacy = 'db'; Canonical = 'artifacts/sqlite + src/common/schema.py'; Reason = 'Review whether migrations remain authoritative.' },
    @{ Legacy = 'system_overview.md'; Canonical = 'docs/system_overview.md'; Reason = 'Root document should be consolidated under docs.' },
    @{ Legacy = 'tectonic_map.md'; Canonical = 'docs/technical/tectonic_map.md'; Reason = 'Root document should be consolidated under docs/technical.' },
    @{ Legacy = 'data_governance.md'; Canonical = 'docs/data_governance.md'; Reason = 'Root document should be consolidated under docs.' },
    @{ Legacy = 'ADR-001-scope-and-positioning.md'; Canonical = 'docs/adr/ADR-001-scope-and-positioning.md'; Reason = 'ADR should live under docs/adr.' },
    @{ Legacy = 'ADR-002-data-authority-sqlite.md'; Canonical = 'docs/adr/ADR-002-data-authority-sqlite.md'; Reason = 'ADR should live under docs/adr.' },
    @{ Legacy = 'ADR-003-open-source-local-first.md'; Canonical = 'docs/adr/ADR-003-open-source-local-first.md'; Reason = 'ADR should live under docs/adr.' }
)

foreach ($entry in $competingAuthorities) {
    $legacyPath = Join-Path $repoRootPath $entry.Legacy
    if (Test-Path -LiteralPath $legacyPath) {
        $manualReview += [pscustomobject]@{
            Path              = (Get-Item -LiteralPath $legacyPath -Force).FullName
            CanonicalTarget   = (Join-Path $repoRootPath $entry.Canonical)
            Reason            = $entry.Reason
            RecommendedAction = 'Consolidate content first, then remove legacy authority.'
        }
    }
}

# Root-level patch/readme residue: do not auto-delete, but list for review.
Get-ChildItem -LiteralPath $repoRootPath -File -Force | Where-Object {
    $_.Name -match '^(README_.*|INSTRUCCIONES_.*|PHASE.*|README_PHASE.*|README_FIX.*|README_.*FIX.*|README_.*PATCH.*)$'
} | ForEach-Object {
    $manualReview += [pscustomobject]@{
        Path              = $_.FullName
        CanonicalTarget   = (Join-Path $repoRootPath 'docs/runbooks or README.md')
        Reason            = 'Patch-era root document competing with canonical docs.'
        RecommendedAction = 'Retain only if still authoritative; otherwise consolidate and remove.'
    }
}

# Deduplicate safe targets by path.
$safeTargets = $safeTargets | Sort-Object Path -Unique
$manualReview = $manualReview | Sort-Object Path -Unique

if ($Apply) {
    foreach ($target in $safeTargets) {
        try {
            if (Test-Path -LiteralPath $target.Path) {
                Remove-Item -LiteralPath $target.Path -Recurse -Force -ErrorAction Stop
                $removed += $target.Path
            }
        }
        catch {
            $errors += ("Failed to remove {0}: {1}" -f $target.Path, $_.Exception.Message)
        }
    }
}

$summary = [pscustomobject]@{
    RepoRoot                = $repoRootPath
    Mode                    = $mode
    TimestampUtc            = (Get-Date).ToUniversalTime().ToString('o')
    SafeTargetsCount        = @($safeTargets).Count
    ManualReviewCount       = @($manualReview).Count
    RemovedCount            = @($removed).Count
    ErrorCount              = @($errors).Count
    SafeTargets             = @($safeTargets)
    ManualReview            = @($manualReview)
    Removed                 = @($removed)
    Errors                  = @($errors)
}

$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonReportPath -Encoding UTF8

$md = @"
# Repository cleanup report

- mode: `$mode`
- repo_root: `$repoRootPath`
- timestamp_utc: `$(Get-Date).ToUniversalTime().ToString('o')`
- safe_targets: $(@($safeTargets).Count)
- manual_review: $(@($manualReview).Count)
- removed: $(@($removed).Count)
- errors: $(@($errors).Count)

## Safe targets
$(New-MarkdownList -Items (@($safeTargets | ForEach-Object { "{0} - {1}" -f $_.Path, $_.Reason })))

## Manual review
$(New-MarkdownList -Items (@($manualReview | ForEach-Object { "{0} => {1} - {2}" -f $_.Path, $_.CanonicalTarget, $_.Reason })))

## Removed
$(New-MarkdownList -Items @($removed))

## Errors
$(New-MarkdownList -Items @($errors))
"@

$md | Set-Content -LiteralPath $mdReportPath -Encoding UTF8

Write-Host "[repo_cleanup] mode=$mode safe_targets=$(@($safeTargets).Count) manual_review=$(@($manualReview).Count) removed=$(@($removed).Count) errors=$(@($errors).Count)"
Write-Host "[repo_cleanup] json=$jsonReportPath"
Write-Host "[repo_cleanup] markdown=$mdReportPath"

if (@($errors).Count -gt 0) {
    exit 1
}
