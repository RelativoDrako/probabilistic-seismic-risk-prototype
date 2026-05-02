[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$ApiBaseUrl = "",
    [string]$WebBaseUrl = ""
)

$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$reportsDir = Join-Path $repoRootPath "artifacts\reports"
if (-not (Test-Path -LiteralPath $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
}

function New-Finding {
    param(
        [string]$Area,
        [string]$Status,
        [string]$Evidence,
        [string]$Action,
        [bool]$Blocking = $false
    )
    [PSCustomObject]@{
        area = $Area
        status = $Status
        evidence = $Evidence
        action = $Action
        blocking = $Blocking
    }
}

function Test-FileExists {
    param([string]$Path)
    return Test-Path -LiteralPath $Path
}

function Test-HttpJson {
    param([string]$Url)
    try {
        $resp = Invoke-RestMethod -Uri $Url -TimeoutSec 8
        return [PSCustomObject]@{ ok = $true; payload = $resp; error = $null }
    } catch {
        return [PSCustomObject]@{ ok = $false; payload = $null; error = $_.Exception.Message }
    }
}

$findings = @()

$requiredDocs = @(
    "docs\publication_surface_requirements.md",
    "docs\publication_surface_target.md",
    "docs\publication_surface_gap_matrix.md"
)

$missingDocs = @($requiredDocs | Where-Object { -not (Test-FileExists (Join-Path $repoRootPath $_)) })
if ($missingDocs.Count -eq 0) {
    $findings += New-Finding -Area "Publication docs" -Status "confirmed" -Evidence "All publication-surface contract documents exist." -Action "Keep them under version control."
} else {
    $findings += New-Finding -Area "Publication docs" -Status "blocking" -Evidence ("Missing docs: " + ($missingDocs -join ", ")) -Action "Add the missing publication-surface contract documents." -Blocking $true
}

$heroPlots = @(
    "artifacts\plots\metrics_panel.png",
    "artifacts\plots\pipeline_trace.png",
    "artifacts\plots\probabilistic_risk_map.png",
    "artifacts\plots\risk_heatmap.png",
    "artifacts\plots\regional_event_counts.png"
)

$missingPlots = @($heroPlots | Where-Object { -not (Test-FileExists (Join-Path $repoRootPath $_)) })
if ($missingPlots.Count -eq 0) {
    $findings += New-Finding -Area "Hero plots" -Status "confirmed" -Evidence "All required hero plot files are present." -Action "Keep current hero plot set for publication."
} else {
    $findings += New-Finding -Area "Hero plots" -Status "blocking" -Evidence ("Missing plot files: " + ($missingPlots -join ", ")) -Action "Generate or restore the missing hero plots." -Blocking $true
}

$heroReports = @(
    "artifacts\reports\demo_evidence.md",
    "artifacts\reports\evaluation_summary.md",
    "artifacts\reports\predemo_status.md",
    "artifacts\reports\class_balance_audit.md"
)

$missingReports = @($heroReports | Where-Object { -not (Test-FileExists (Join-Path $repoRootPath $_)) })
if ($missingReports.Count -eq 0) {
    $findings += New-Finding -Area "Hero reports" -Status "confirmed" -Evidence "All required hero reports are present." -Action "Keep current hero report set for publication."
} else {
    $findings += New-Finding -Area "Hero reports" -Status "blocking" -Evidence ("Missing report files: " + ($missingReports -join ", ")) -Action "Restore or regenerate the missing hero reports." -Blocking $true
}

$webAppPath = Join-Path $repoRootPath "src\web\app.py"
$apiMainPath = Join-Path $repoRootPath "src\api\main.py"
$apiRepoPath = Join-Path $repoRootPath "src\api\repository.py"

if (-not (Test-FileExists $webAppPath)) {
    $findings += New-Finding -Area "Web app" -Status "blocking" -Evidence "src/web/app.py is missing." -Action "Restore src/web/app.py." -Blocking $true
} else {
    $webText = Get-Content -LiteralPath $webAppPath -Raw -Encoding UTF8
    $requiredLabels = @(
        "Executive Overview",
        "Mexico Executive Map",
        "Regional Risk View",
        "Model Evaluation",
        "Technical Raw Views",
        "Most Affected Zones",
        "Historical Major Events (Reference Only)",
        "Recent Significant Events"
    )
    $missingLabels = @($requiredLabels | Where-Object { $webText -notmatch [regex]::Escape($_) })
    if ($missingLabels.Count -eq 0) {
        $findings += New-Finding -Area "Web publication sections" -Status "confirmed" -Evidence "All required public section labels are present in src/web/app.py." -Action "Preserve section hierarchy."
    } else {
        $findings += New-Finding -Area "Web publication sections" -Status "blocking" -Evidence ("Missing section labels: " + ($missingLabels -join ", ")) -Action "Reinstate the missing public-facing sections." -Blocking $true
    }
}

if (-not (Test-FileExists $apiMainPath)) {
    $findings += New-Finding -Area "API main" -Status "blocking" -Evidence "src/api/main.py is missing." -Action "Restore src/api/main.py." -Blocking $true
} else {
    $apiText = Get-Content -LiteralPath $apiMainPath -Raw -Encoding UTF8
    $requiredApiRoutes = @("/health", "/summary/latest", "/evaluation/latest", "/executive/mexico-map")
    $missingRoutes = @($requiredApiRoutes | Where-Object { $apiText -notmatch [regex]::Escape($_) })
    if ($missingRoutes.Count -eq 0) {
        $findings += New-Finding -Area "API publication routes" -Status "confirmed" -Evidence "All required publication routes are declared in src/api/main.py." -Action "Keep current route surface."
    } else {
        $findings += New-Finding -Area "API publication routes" -Status "blocking" -Evidence ("Missing API routes: " + ($missingRoutes -join ", ")) -Action "Restore the missing API routes." -Blocking $true
    }
}

if (-not (Test-FileExists $apiRepoPath)) {
    $findings += New-Finding -Area "API repository" -Status "blocking" -Evidence "src/api/repository.py is missing." -Action "Restore src/api/repository.py." -Blocking $true
} else {
    $repoText = Get-Content -LiteralPath $apiRepoPath -Raw -Encoding UTF8
    $requiredSemantics = @("reference_geography", "political_division", "tectonic_layer", "executive_risk_index")
    $missingSemantics = @($requiredSemantics | Where-Object { $repoText -notmatch [regex]::Escape($_) })
    if ($missingSemantics.Count -eq 0) {
        $findings += New-Finding -Area "Geographic semantics" -Status "confirmed" -Evidence "Geographic/public semantic fields are implemented in src/api/repository.py." -Action "Keep current enrichment logic under audit."
    } else {
        $findings += New-Finding -Area "Geographic semantics" -Status "blocking" -Evidence ("Missing semantic field handling: " + ($missingSemantics -join ", ")) -Action "Add or restore geographic/public semantic enrichment." -Blocking $true
    }
}

if (-not [string]::IsNullOrWhiteSpace($ApiBaseUrl)) {
    $health = Test-HttpJson -Url ($ApiBaseUrl.TrimEnd("/") + "/health")
    $summary = Test-HttpJson -Url ($ApiBaseUrl.TrimEnd("/") + "/summary/latest")
    $evaluation = Test-HttpJson -Url ($ApiBaseUrl.TrimEnd("/") + "/evaluation/latest")
    $mexicoMap = Test-HttpJson -Url ($ApiBaseUrl.TrimEnd("/") + "/executive/mexico-map")

    if ($health.ok -and $summary.ok -and $evaluation.ok -and $mexicoMap.ok) {
        $findings += New-Finding -Area "Live API endpoints" -Status "confirmed" -Evidence "All required publication endpoints responded successfully." -Action "Keep smoke test in release gate."
    } else {
        $errors = @()
        if (-not $health.ok) { $errors += "/health" }
        if (-not $summary.ok) { $errors += "/summary/latest" }
        if (-not $evaluation.ok) { $errors += "/evaluation/latest" }
        if (-not $mexicoMap.ok) { $errors += "/executive/mexico-map" }
        $findings += New-Finding -Area "Live API endpoints" -Status "blocking" -Evidence ("Failed endpoints: " + ($errors -join ", ")) -Action "Repair the failed publication endpoints before publishing." -Blocking $true
    }

    if ($mexicoMap.ok) {
        $payload = $mexicoMap.payload
        $regions = @($payload.regions)
        $topZones = @($payload.top_affected_zones)
        $notable = @($payload.notable_events)

        $geoFailures = @()

        foreach ($item in $regions[0..([Math]::Min($regions.Count,3)-1)]) {
            if ([string]::IsNullOrWhiteSpace([string]$item.reference_geography) -or [string]::IsNullOrWhiteSpace([string]$item.political_division) -or [string]::IsNullOrWhiteSpace([string]$item.tectonic_layer)) {
                $geoFailures += "regions"
                break
            }
        }
        foreach ($item in $topZones[0..([Math]::Min($topZones.Count,3)-1)]) {
            if ([string]::IsNullOrWhiteSpace([string]$item.reference_geography) -or [string]::IsNullOrWhiteSpace([string]$item.political_division) -or [string]::IsNullOrWhiteSpace([string]$item.tectonic_layer)) {
                $geoFailures += "top_affected_zones"
                break
            }
        }
        foreach ($item in $notable[0..([Math]::Min($notable.Count,3)-1)]) {
            if ([string]::IsNullOrWhiteSpace([string]$item.reference_geography) -or [string]::IsNullOrWhiteSpace([string]$item.political_division) -or [string]::IsNullOrWhiteSpace([string]$item.tectonic_layer)) {
                $geoFailures += "notable_events"
                break
            }
        }

        if ($geoFailures.Count -eq 0) {
            $findings += New-Finding -Area "Live map semantics" -Status "confirmed" -Evidence "Sampled live map payload items include readable geography and tectonic context." -Action "Keep current semantics in publication surface."
        } else {
            $findings += New-Finding -Area "Live map semantics" -Status "blocking" -Evidence ("Null-like geographic fields detected in: " + (($geoFailures | Select-Object -Unique) -join ", ")) -Action "Repair payload fallbacks before publishing the web surface." -Blocking $true
        }
    }
}

if (-not [string]::IsNullOrWhiteSpace($WebBaseUrl)) {
    try {
        $resp = Invoke-WebRequest -Uri $WebBaseUrl -TimeoutSec 8 -UseBasicParsing
        $findings += New-Finding -Area "Live web root" -Status "confirmed" -Evidence ("Web root responded with status " + [string]$resp.StatusCode + ".") -Action "Retain web smoke test in release gate."
    } catch {
        $findings += New-Finding -Area "Live web root" -Status "blocking" -Evidence ("Web root failed: " + $_.Exception.Message) -Action "Repair the web publication surface before publishing." -Blocking $true
    }
}

$blockingCount = @($findings | Where-Object { $_.blocking }).Count
$warningCount = @($findings | Where-Object { -not $_.blocking -and $_.status -ne "confirmed" }).Count
$overall = if ($blockingCount -gt 0) { "BLOCKED" } else { "READY_FOR_NEXT_STAGE" }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonPath = Join-Path $reportsDir ("publication_surface_audit_{0}.json" -f $timestamp)
$mdPath = Join-Path $reportsDir ("publication_surface_audit_{0}.md" -f $timestamp)

$payload = [PSCustomObject]@{
    repo_root = $repoRootPath
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
    overall_status = $overall
    blocking_count = $blockingCount
    warning_count = $warningCount
    findings = $findings
}

$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$lines = @()
$lines += "# Publication Surface Audit"
$lines += ""
$lines += "- overall_status: `"$overall`""
$lines += "- blocking_count: $blockingCount"
$lines += "- warning_count: $warningCount"
$lines += ""
$lines += "## Findings"
foreach ($item in $findings) {
    $lines += ("- **{0}** | status={1} | blocking={2}" -f $item.area, $item.status, $item.blocking)
    $lines += ("  - evidence: {0}" -f $item.evidence)
    $lines += ("  - action: {0}" -f $item.action)
}
$lines -join [Environment]::NewLine | Set-Content -LiteralPath $mdPath -Encoding UTF8

Write-Host ("[audit_publication_surface] json={0}" -f $jsonPath)
Write-Host ("[audit_publication_surface] markdown={0}" -f $mdPath)
Write-Host ("[audit_publication_surface] overall={0}" -f $overall)
