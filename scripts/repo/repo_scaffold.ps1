[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = ".",

    [Parameter(Mandatory = $false)]
    [switch]$CreateStubs,

    [Parameter(Mandatory = $false)]
    [switch]$Force
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
        return $true
    }
    return $false
}

function Write-StubIfMissing {
    param(
        [string]$Path,
        [string]$Content,
        [switch]$ForceWrite
    )

    if ((-not (Test-Path -LiteralPath $Path)) -or $ForceWrite) {
        $parent = Split-Path -Parent $Path
        if ($parent) {
            [void](New-Item -ItemType Directory -Path $parent -Force)
        }
        $Content | Set-Content -LiteralPath $Path -Encoding UTF8
        return $true
    }
    return $false
}

$repoRootPath = Resolve-CanonicalPath -Path $RepoRoot
$reportsDir = Join-Path $repoRootPath 'artifacts/reports'
[void](New-Item -ItemType Directory -Path $reportsDir -Force)
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$jsonReportPath = Join-Path $reportsDir ("repo_scaffold_report_{0}.json" -f $timestamp)
$mdReportPath = Join-Path $reportsDir ("repo_scaffold_report_{0}.md" -f $timestamp)

$createdDirs = @()
$createdFiles = @()
$existing = @()

$canonicalDirs = @(
    'docs',
    'docs/architecture',
    'docs/technical',
    'docs/adr',
    'docs/runbooks',
    'src',
    'src/api',
    'src/web',
    'scripts',
    'scripts/repo',
    'artifacts',
    'artifacts/models',
    'artifacts/plots',
    'artifacts/reports',
    'artifacts/sqlite',
    'data',
    'presentations',
    'presentations/slides',
    'presentations/assets'
)

foreach ($relativeDir in $canonicalDirs) {
    $fullPath = Join-Path $repoRootPath $relativeDir
    if (Ensure-Directory -Path $fullPath) {
        $createdDirs += $fullPath
    }
    else {
        $existing += $fullPath
    }
}

if ($CreateStubs) {
    $stubs = @(
        @{ Path = 'docs/how_to_read.md'; Content = @"
# How to read this repository

This repository is organized around four public authorities:

- `docs/` for public documentation
- `src/` for implementation
- `artifacts/` for generated evidence
- `presentations/` for supporting visual material

Read order:
1. `README.md`
2. `DISCLAIMER.md`
3. `HOW_TO_RUN.md`
4. `docs/architecture.md`
5. `docs/data_governance.md`
"@ },
        @{ Path = 'docs/system_overview.md'; Content = @"
# System overview

This prototype is local-first, open-source-only, and bounded in scope.

Core surfaces:
- ingestion and curation pipeline
- SQLite prototype authority
- API and web demo surfaces for specialized queries
- artifacts for evidence and reproducibility
"@ },
        @{ Path = 'docs/technical/model_limitations.md'; Content = @"
# Model limitations

- exploratory probabilistic prototype only
- not an earthquake prediction system
- depends on catalog stability and curation quality
- scientific interpretation must remain conservative
"@ },
        @{ Path = 'docs/technical/lessons_learned.md'; Content = @"
# Lessons learned

- catalog governance matters as much as model choice
- idempotent local pipelines reduce ambiguity
- weak signal analysis requires strict interpretation discipline
"@ },
        @{ Path = 'docs/model_card.md'; Content = @"
# Model card

## Intended use
Exploratory probabilistic regional seismic risk analysis for Mexico.

## Out of scope
- official warning system
- deterministic prediction
- production deployment
"@ },
        @{ Path = 'data/README_dataset.md'; Content = @"
# Dataset README

Document here:
- canonical sources
- query parameters
- time range
- refresh procedure
- immutable raw evidence policy
"@ },
        @{ Path = 'docs/adr/ADR-001-scope-and-positioning.md'; Content = @"
# ADR-001 - Scope and positioning

Status: draft

This file should consolidate the canonical scope and positioning decision.
"@ },
        @{ Path = 'docs/adr/ADR-002-data-authority-sqlite.md'; Content = @"
# ADR-002 - Data authority: SQLite

Status: draft

This file should consolidate the canonical SQLite authority decision.
"@ },
        @{ Path = 'docs/adr/ADR-003-open-source-local-first.md'; Content = @"
# ADR-003 - Open source and local-first

Status: draft

This file should consolidate the canonical open-source local-first decision.
"@ }
    )

    foreach ($stub in $stubs) {
        $fullPath = Join-Path $repoRootPath $stub.Path
        if (Write-StubIfMissing -Path $fullPath -Content $stub.Content -ForceWrite:$Force) {
            $createdFiles += $fullPath
        }
        else {
            $existing += $fullPath
        }
    }
}

$summary = [pscustomobject]@{
    RepoRoot          = $repoRootPath
    TimestampUtc      = (Get-Date).ToUniversalTime().ToString('o')
    CreateStubs       = [bool]$CreateStubs
    Force             = [bool]$Force
    CreatedDirsCount  = @($createdDirs).Count
    CreatedFilesCount = @($createdFiles).Count
    CreatedDirs       = @($createdDirs)
    CreatedFiles      = @($createdFiles)
    ExistingPaths     = @($existing | Sort-Object -Unique)
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonReportPath -Encoding UTF8

$md = @"
# Repository scaffold report

- repo_root: `$repoRootPath`
- timestamp_utc: `$(Get-Date).ToUniversalTime().ToString('o')`
- create_stubs: $([bool]$CreateStubs)
- force: $([bool]$Force)
- created_dirs: $(@($createdDirs).Count)
- created_files: $(@($createdFiles).Count)

## Created directories
$((@($createdDirs) | ForEach-Object { "- $_" }) -join [Environment]::NewLine)

## Created files
$(if (@($createdFiles).Count -gt 0) { ((@($createdFiles) | ForEach-Object { "- $_" }) -join [Environment]::NewLine) } else { '- none' })
"@

$md | Set-Content -LiteralPath $mdReportPath -Encoding UTF8

Write-Host "[repo_scaffold] created_dirs=$(@($createdDirs).Count) created_files=$(@($createdFiles).Count)"
Write-Host "[repo_scaffold] json=$jsonReportPath"
Write-Host "[repo_scaffold] markdown=$mdReportPath"
