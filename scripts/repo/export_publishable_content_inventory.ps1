[CmdletBinding()]
param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$reportsDir = Join-Path $repoRootPath "artifacts\reports"
$plotsDir = Join-Path $repoRootPath "artifacts\plots"

$reports = @()
if (Test-Path -LiteralPath $reportsDir) {
    $reports = @(Get-ChildItem -LiteralPath $reportsDir -File | Sort-Object Name)
}
$plots = @()
if (Test-Path -LiteralPath $plotsDir) {
    $plots = @(Get-ChildItem -LiteralPath $plotsDir -File | Sort-Object Name)
}

$recommendedHeroPlots = @()
foreach ($name in @("metrics_panel.png", "pipeline_trace.png", "probabilistic_risk_map.png", "risk_heatmap.png", "regional_event_counts.png")) {
    $candidate = $plots | Where-Object { $_.Name -eq $name } | Select-Object -First 1
    if ($null -ne $candidate) { $recommendedHeroPlots += $candidate.Name }
}

$recommendedHeroReports = @()
foreach ($name in @("demo_evidence.md", "evaluation_summary.md", "predemo_status.md", "class_balance_audit.md")) {
    $candidate = $reports | Where-Object { $_.Name -eq $name } | Select-Object -First 1
    if ($null -ne $candidate) { $recommendedHeroReports += $candidate.Name }
}

$payload = [PSCustomObject]@{
    RepoRoot = $repoRootPath
    TimestampUtc = (Get-Date).ToUniversalTime().ToString("o")
    PlotCount = $plots.Count
    ReportCount = $reports.Count
    HeroPlotCandidates = $recommendedHeroPlots
    HeroReportCandidates = $recommendedHeroReports
    Plots = @($plots | ForEach-Object {
        [PSCustomObject]@{
            Name = $_.Name
            RelativePath = ("artifacts/plots/{0}" -f $_.Name)
            SizeBytes = $_.Length
        }
    })
    Reports = @($reports | ForEach-Object {
        [PSCustomObject]@{
            Name = $_.Name
            RelativePath = ("artifacts/reports/{0}" -f $_.Name)
            SizeBytes = $_.Length
        }
    })
}

$reportsOutDir = Join-Path $repoRootPath "artifacts\reports"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonPath = Join-Path $reportsOutDir ("publishable_content_inventory_{0}.json" -f $timestamp)
$mdPath = Join-Path $reportsOutDir ("publishable_content_inventory_{0}.md" -f $timestamp)

$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$lines = @()
$lines += "# Publishable Content Inventory"
$lines += ""
$lines += "- repo_root: `"$repoRootPath`""
$lines += "- timestamp_utc: `"$($payload.TimestampUtc)`""
$lines += "- plot_count: $($payload.PlotCount)"
$lines += "- report_count: $($payload.ReportCount)"
$lines += ""
$lines += "## Hero Plot Candidates"
if ($payload.HeroPlotCandidates.Count -eq 0) {
    $lines += "- none"
} else {
    foreach ($x in $payload.HeroPlotCandidates) { $lines += ("- {0}" -f $x) }
}
$lines += ""
$lines += "## Hero Report Candidates"
if ($payload.HeroReportCandidates.Count -eq 0) {
    $lines += "- none"
} else {
    foreach ($x in $payload.HeroReportCandidates) { $lines += ("- {0}" -f $x) }
}
$lines += ""
$lines += "## All Plot Files"
foreach ($plot in $payload.Plots) {
    $lines += ("- {0} ({1} bytes)" -f $plot.RelativePath, $plot.SizeBytes)
}
$lines += ""
$lines += "## All Report Files"
foreach ($report in $payload.Reports) {
    $lines += ("- {0} ({1} bytes)" -f $report.RelativePath, $report.SizeBytes)
}
$lines -join [Environment]::NewLine | Set-Content -LiteralPath $mdPath -Encoding UTF8

Write-Host ("[export_publishable_content_inventory] json={0}" -f $jsonPath)
Write-Host ("[export_publishable_content_inventory] markdown={0}" -f $mdPath)
