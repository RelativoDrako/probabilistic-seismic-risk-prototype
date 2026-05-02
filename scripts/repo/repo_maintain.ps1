[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = ".",

    [Parameter(Mandatory = $false)]
    [switch]$Apply,

    [Parameter(Mandatory = $false)]
    [switch]$CreateStubs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-CanonicalPath {
    param([string]$Path)
    $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
    return $resolved.Path
}

$repoRootPath = Resolve-CanonicalPath -Path $RepoRoot
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$cleanupScript = Join-Path $scriptRoot 'repo_cleanup.ps1'
$scaffoldScript = Join-Path $scriptRoot 'repo_scaffold.ps1'
$validateScript = Join-Path $scriptRoot 'repo_validate.ps1'
$reportsDir = Join-Path $repoRootPath 'artifacts/reports'
[void](New-Item -ItemType Directory -Path $reportsDir -Force)
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$summaryPath = Join-Path $reportsDir ("repo_maintenance_summary_{0}.md" -f $timestamp)

$steps = @()
$overallSuccess = $true

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    try {
        & $Action
        $script:steps += [pscustomobject]@{ Step = $Name; Status = 'PASS' }
    }
    catch {
        $script:steps += [pscustomobject]@{ Step = $Name; Status = 'FAIL'; Detail = $_.Exception.Message }
        $script:overallSuccess = $false
        throw
    }
}

try {
    Invoke-Step -Name 'cleanup-dryrun' -Action {
        $global:LASTEXITCODE = 0
        & $cleanupScript -RepoRoot $repoRootPath -DryRun
        if ($LASTEXITCODE -ne 0) { throw "cleanup-dryrun failed with exit code $LASTEXITCODE" }
    }

    if ($Apply) {
        Invoke-Step -Name 'cleanup-apply' -Action {
            $global:LASTEXITCODE = 0
            & $cleanupScript -RepoRoot $repoRootPath -Apply
            if ($LASTEXITCODE -ne 0) { throw "cleanup-apply failed with exit code $LASTEXITCODE" }
        }
    }

    Invoke-Step -Name 'scaffold' -Action {
        $global:LASTEXITCODE = 0
        & $scaffoldScript -RepoRoot $repoRootPath -CreateStubs:$CreateStubs
        if ($LASTEXITCODE -ne 0) { throw "scaffold failed with exit code $LASTEXITCODE" }
    }

    Invoke-Step -Name 'validate' -Action {
        $global:LASTEXITCODE = 0
        & $validateScript -RepoRoot $repoRootPath
        if ($LASTEXITCODE -ne 0) { throw "validate failed with exit code $LASTEXITCODE" }
    }
}
finally {
    $status = if ($overallSuccess) { 'PASS' } else { 'FAIL' }
    $lines = @(
        '# Repository maintenance summary',
        '',
        ('- repo_root: `{0}`' -f $repoRootPath),
        ('- timestamp_utc: `{0}`' -f (Get-Date).ToUniversalTime().ToString('o')),
        ('- apply: {0}' -f [bool]$Apply),
        ('- create_stubs: {0}' -f [bool]$CreateStubs),
        ('- status: **{0}**' -f $status),
        '',
        '## Steps'
    )

    foreach ($step in $steps) {
        $detail = if ($step.PSObject.Properties.Name -contains 'Detail') { " - $($step.Detail)" } else { '' }
        $lines += ('- {0}: {1}{2}' -f $step.Step, $step.Status, $detail)
    }

    $lines -join [Environment]::NewLine | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Write-Host "[repo_maintain] status=$status summary=$summaryPath"
}

if (-not $overallSuccess) {
    exit 1
}
