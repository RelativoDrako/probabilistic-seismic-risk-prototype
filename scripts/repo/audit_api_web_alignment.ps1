[CmdletBinding()]
param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

function New-StatusObject {
    param(
        [string]$Area,
        [string]$Status,
        [string]$Evidence,
        [string]$Recommendation
    )
    [PSCustomObject]@{
        Area = $Area
        Status = $Status
        Evidence = $Evidence
        Recommendation = $Recommendation
    }
}

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$reportsDir = Join-Path $repoRootPath "artifacts\reports"
if (-not (Test-Path -LiteralPath $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
}

$apiMainPath = Join-Path $repoRootPath "src\api\main.py"
$apiRepoPath = Join-Path $repoRootPath "src\api\repository.py"
$webAppPath = Join-Path $repoRootPath "src\web\app.py"
$webRepoPath = Join-Path $repoRootPath "src\web\repository.py"
$plotsDir = Join-Path $repoRootPath "artifacts\plots"
$reportFilesDir = Join-Path $repoRootPath "artifacts\reports"
$sqliteDir = Join-Path $repoRootPath "artifacts\sqlite"

$statuses = @()

$apiMainExists = Test-Path -LiteralPath $apiMainPath
$webAppExists = Test-Path -LiteralPath $webAppPath
$apiRepoExists = Test-Path -LiteralPath $apiRepoPath
$webRepoExists = Test-Path -LiteralPath $webRepoPath
$sqliteExists = Test-Path -LiteralPath $sqliteDir

$apiMainText = if ($apiMainExists) { Get-Content -LiteralPath $apiMainPath -Raw -Encoding UTF8 } else { "" }
$apiRepoText = if ($apiRepoExists) { Get-Content -LiteralPath $apiRepoPath -Raw -Encoding UTF8 } else { "" }
$webAppText = if ($webAppExists) { Get-Content -LiteralPath $webAppPath -Raw -Encoding UTF8 } else { "" }
$webRepoText = if ($webRepoExists) { Get-Content -LiteralPath $webRepoPath -Raw -Encoding UTF8 } else { "" }

$endpointMatches = @()
if ($apiMainExists) {
    $endpointMatches = [regex]::Matches($apiMainText, '@app\.(get|post|put|delete|patch)\("([^"]+)"')
}
$endpointPaths = @($endpointMatches | ForEach-Object { $_.Groups[2].Value })

$plotFiles = @()
if (Test-Path -LiteralPath $plotsDir) {
    $plotFiles = @(Get-ChildItem -LiteralPath $plotsDir -File -ErrorAction SilentlyContinue)
}
$reportFiles = @()
if (Test-Path -LiteralPath $reportFilesDir) {
    $reportFiles = @(Get-ChildItem -LiteralPath $reportFilesDir -File -ErrorAction SilentlyContinue)
}

$usesFastApi = $apiMainText -match 'FastAPI'
$usesStreamlit = $webAppText -match 'streamlit'
$usesSQLiteAccess = ($apiRepoText -match 'sqlite' -or $apiRepoText -match 'managed_connection' -or $webRepoText -match 'managed_connection')

$hasHealth = $endpointPaths -contains '/health'
$hasSummary = $endpointPaths -contains '/summary/latest'
$hasRegion = $endpointPaths -contains '/regions/{region_code}/latest'
$hasEvaluation = $endpointPaths -contains '/evaluation/latest'

$usesJsonInWeb = $webAppText -match 'st\.json'
$usesImagesInWeb = $webAppText -match 'st\.image'
$usesMarkdownInWeb = $webAppText -match 'st\.markdown' -or $webAppText -match 'st\.write'
$usesTabsInWeb = $webAppText -match 'st\.tabs'
$usesSelectbox = $webAppText -match 'st\.selectbox'

if ($apiMainExists -and $usesFastApi) {
    $statuses += New-StatusObject -Area "API surface exists" -Status "confirmed" -Evidence "src/api/main.py uses FastAPI." -Recommendation "Keep as the canonical prototype API entrypoint."
} else {
    $statuses += New-StatusObject -Area "API surface exists" -Status "absent" -Evidence "FastAPI entrypoint was not confirmed." -Recommendation "Create or repair src/api/main.py before presenting API capability."
}

if ($hasHealth -and $hasSummary -and $hasRegion -and $hasEvaluation) {
    $statuses += New-StatusObject -Area "Core API endpoints" -Status "confirmed" -Evidence ("Confirmed endpoints: " + (($endpointPaths | Sort-Object) -join ", ")) -Recommendation "Document only these stable endpoints publicly unless new ones are implemented."
} elseif ($endpointPaths.Count -gt 0) {
    $statuses += New-StatusObject -Area "Core API endpoints" -Status "partial" -Evidence ("Detected endpoints: " + (($endpointPaths | Sort-Object) -join ", ")) -Recommendation "Fill the missing summary/region/evaluation routes or narrow public claims."
} else {
    $statuses += New-StatusObject -Area "Core API endpoints" -Status "absent" -Evidence "No API routes were detected." -Recommendation "Do not claim API consumption capability until routes exist."
}

if ($webAppExists -and $usesStreamlit) {
    $statuses += New-StatusObject -Area "Web surface exists" -Status "confirmed" -Evidence "src/web/app.py uses Streamlit." -Recommendation "Keep Streamlit as the lightweight prototype presentation surface."
} else {
    $statuses += New-StatusObject -Area "Web surface exists" -Status "absent" -Evidence "No Streamlit entrypoint was confirmed." -Recommendation "Create or repair src/web/app.py before presenting a web surface."
}

if ($usesTabsInWeb -and $usesJsonInWeb -and $usesSelectbox) {
    $statuses += New-StatusObject -Area "Current web interaction model" -Status "confirmed" -Evidence "The web surface already has tabbed JSON-based views and region selection." -Recommendation "Treat the current UI as a technical viewer baseline, not as the final public-facing impact surface."
} elseif ($webAppExists) {
    $statuses += New-StatusObject -Area "Current web interaction model" -Status "partial" -Evidence "A web app exists, but tabs, selectors, or JSON rendering are incomplete." -Recommendation "Establish at least overview, region, and evaluation views."
}

if ($plotFiles.Count -gt 0 -and -not $usesImagesInWeb) {
    $statuses += New-StatusObject -Area "Plot publication in web" -Status "partial" -Evidence ("Artifacts/plots contains " + $plotFiles.Count + " file(s), but st.image was not detected in src/web/app.py.") -Recommendation "Add explicit plot panels for metrics, pipeline trace, risk map, and regional counts."
} elseif ($plotFiles.Count -gt 0 -and $usesImagesInWeb) {
    $statuses += New-StatusObject -Area "Plot publication in web" -Status "confirmed" -Evidence ("Plot files are present and st.image is already used.") -Recommendation "Ensure the web highlights only the strongest visuals."
} else {
    $statuses += New-StatusObject -Area "Plot publication in web" -Status "absent" -Evidence "Plots were not found or the web has no image rendering path." -Recommendation "Do not frame the web surface as a results publication page yet."
}

if ($reportFiles.Count -gt 0 -and -not $usesMarkdownInWeb) {
    $statuses += New-StatusObject -Area "Report publication in web" -Status "partial" -Evidence ("Artifacts/reports contains " + $reportFiles.Count + " file(s), but rich markdown/report rendering was not detected.") -Recommendation "Add report summary cards or selected markdown sections instead of only raw JSON."
} elseif ($reportFiles.Count -gt 0 -and $usesMarkdownInWeb) {
    $statuses += New-StatusObject -Area "Report publication in web" -Status "confirmed" -Evidence "Report artifacts exist and the web surface contains a markdown-capable rendering path." -Recommendation "Limit rendered text to curated executive content."
} else {
    $statuses += New-StatusObject -Area "Report publication in web" -Status "absent" -Evidence "Report artifacts were not confirmed or the web has no report rendering path." -Recommendation "Avoid promising report publication through the web surface."
}

if ($usesSQLiteAccess -and $sqliteExists) {
    $statuses += New-StatusObject -Area "SQLite-backed persistence" -Status "confirmed" -Evidence "Repository code uses managed_connection/create_schema and artifacts/sqlite exists." -Recommendation "Keep SQLite as the read authority for API/web surfaces."
} else {
    $statuses += New-StatusObject -Area "SQLite-backed persistence" -Status "partial" -Evidence "The code or folder structure does not fully confirm SQLite-backed reads." -Recommendation "Avoid loose file-based reads for published surfaces."
}

$highlightPlots = @()
$preferredPlotNames = @(
    "metrics_panel.png",
    "pipeline_trace.png",
    "probabilistic_risk_map.png",
    "risk_heatmap.png",
    "regional_event_counts.png"
)
foreach ($name in $preferredPlotNames) {
    $candidate = Join-Path $plotsDir $name
    if (Test-Path -LiteralPath $candidate) {
        $highlightPlots += $name
    }
}

$preferredReports = @(
    "demo_evidence.md",
    "evaluation_summary.md",
    "predemo_status.md",
    "class_balance_audit.md"
)
$highlightReports = @()
foreach ($name in $preferredReports) {
    $candidate = Join-Path $reportFilesDir $name
    if (Test-Path -LiteralPath $candidate) {
        $highlightReports += $name
    }
}

$summary = [PSCustomObject]@{
    RepoRoot = $repoRootPath
    TimestampUtc = (Get-Date).ToUniversalTime().ToString("o")
    EndpointCount = $endpointPaths.Count
    Endpoints = $endpointPaths
    PlotCount = $plotFiles.Count
    ReportCount = $reportFiles.Count
    HighlightPlots = $highlightPlots
    HighlightReports = $highlightReports
    SurfacePositioning = "The current API/web layer is real and functional, but the web surface is still closer to a technical viewer than to a high-impact publication page."
    RecommendedWebSections = @(
        "Executive overview cards",
        "Regional risk visuals",
        "Model evaluation panel",
        "Selected report summaries",
        "Explicit limitations and disclaimer"
    )
    Statuses = $statuses
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonPath = Join-Path $reportsDir ("api_web_alignment_report_{0}.json" -f $timestamp)
$mdPath = Join-Path $reportsDir ("api_web_alignment_report_{0}.md" -f $timestamp)

$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$lines = @()
$lines += "# API and Web Alignment Report"
$lines += ""
$lines += "- repo_root: `"$repoRootPath`""
$lines += "- timestamp_utc: `"$($summary.TimestampUtc)`""
$lines += "- endpoint_count: $($summary.EndpointCount)"
$lines += "- plot_count: $($summary.PlotCount)"
$lines += "- report_count: $($summary.ReportCount)"
$lines += ""
$lines += "## Current Positioning"
$lines += $summary.SurfacePositioning
$lines += ""
$lines += "## Status Matrix"
foreach ($item in $statuses) {
    $lines += ("- **{0}**: {1}" -f $item.Area, $item.Status)
    $lines += ("  - evidence: {0}" -f $item.Evidence)
    $lines += ("  - recommendation: {0}" -f $item.Recommendation)
}
$lines += ""
$lines += "## Highlight Plot Candidates"
if ($highlightPlots.Count -eq 0) {
    $lines += "- none"
} else {
    foreach ($plot in $highlightPlots) { $lines += ("- {0}" -f $plot) }
}
$lines += ""
$lines += "## Highlight Report Candidates"
if ($highlightReports.Count -eq 0) {
    $lines += "- none"
} else {
    foreach ($report in $highlightReports) { $lines += ("- {0}" -f $report) }
}
$lines += ""
$lines += "## Recommended Web Sections"
foreach ($section in $summary.RecommendedWebSections) {
    $lines += ("- {0}" -f $section)
}
$lines -join [Environment]::NewLine | Set-Content -LiteralPath $mdPath -Encoding UTF8

Write-Host ("[audit_api_web_alignment] json={0}" -f $jsonPath)
Write-Host ("[audit_api_web_alignment] markdown={0}" -f $mdPath)
