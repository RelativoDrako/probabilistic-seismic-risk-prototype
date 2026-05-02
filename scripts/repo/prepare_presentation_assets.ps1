[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$ScreenshotDir = "",
    [switch]$Overwrite
)

$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Copy-SelectedFile {
    param(
        [string]$SourcePath,
        [string]$DestinationPath,
        [switch]$Overwrite
    )

    if (-not (Test-Path -LiteralPath $SourcePath)) {
        return [PSCustomObject]@{
            status = "missing"
            source = $SourcePath
            destination = $DestinationPath
        }
    }

    $destDir = Split-Path -Parent $DestinationPath
    Ensure-Dir -Path $destDir

    if ((Test-Path -LiteralPath $DestinationPath) -and (-not $Overwrite)) {
        return [PSCustomObject]@{
            status = "kept"
            source = $SourcePath
            destination = $DestinationPath
        }
    }

    Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
    return [PSCustomObject]@{
        status = "copied"
        source = $SourcePath
        destination = $DestinationPath
    }
}

$assetsRoot = Join-Path $repoRootPath "presentations\assets"
$plotsOut = Join-Path $assetsRoot "plots"
$reportsOut = Join-Path $assetsRoot "reports"
$capturesOut = Join-Path $assetsRoot "web_captures"
$metadataOut = Join-Path $assetsRoot "metadata"

Ensure-Dir $assetsRoot
Ensure-Dir $plotsOut
Ensure-Dir $reportsOut
Ensure-Dir $capturesOut
Ensure-Dir $metadataOut

$plotSelections = @(
    @{ source = "artifacts\plots\metrics_panel.png"; target = "01_metrics_panel.png"; title = "Metrics panel"; usage = "Primary executive metrics visual" },
    @{ source = "artifacts\plots\pipeline_trace.png"; target = "02_pipeline_trace.png"; title = "Pipeline trace"; usage = "Traceability and workflow evidence" },
    @{ source = "artifacts\plots\probabilistic_risk_map.png"; target = "03_probabilistic_risk_map.png"; title = "Regional analytical result" },
    @{ source = "artifacts\plots\risk_heatmap.png"; target = "04_risk_heatmap.png"; title = "Risk heatmap"; usage = "Risk concentration reference" },
    @{ source = "artifacts\plots\regional_event_counts.png"; target = "05_regional_event_counts.png"; title = "Regional event counts"; usage = "Regional activity comparison" }
)

$reportSelections = @(
    @{ source = "artifacts\reports\demo_evidence.md"; target = "01_demo_evidence.md"; title = "Demo evidence"; usage = "Executive evidence summary" },
    @{ source = "artifacts\reports\evaluation_summary.md"; target = "02_evaluation_summary.md"; title = "Evaluation summary"; usage = "Model evaluation summary" },
    @{ source = "artifacts\reports\predemo_status.md"; target = "03_predemo_status.md"; title = "Predemo status"; usage = "Pre-demo operational status" },
    @{ source = "artifacts\reports\class_balance_audit.md"; target = "04_class_balance_audit.md"; title = "Class balance audit"; usage = "Dataset balance explanation" }
)

$copyResults = @()
foreach ($item in $plotSelections) {
    $sourcePath = Join-Path $repoRootPath $item.source
    $destinationPath = Join-Path $plotsOut $item.target
    $result = Copy-SelectedFile -SourcePath $sourcePath -DestinationPath $destinationPath -Overwrite:$Overwrite
    $result | Add-Member -NotePropertyName category -NotePropertyValue "plot"
    $result | Add-Member -NotePropertyName title -NotePropertyValue $item.title
    $result | Add-Member -NotePropertyName usage -NotePropertyValue $item.usage
    $copyResults += $result
}

foreach ($item in $reportSelections) {
    $sourcePath = Join-Path $repoRootPath $item.source
    $destinationPath = Join-Path $reportsOut $item.target
    $result = Copy-SelectedFile -SourcePath $sourcePath -DestinationPath $destinationPath -Overwrite:$Overwrite
    $result | Add-Member -NotePropertyName category -NotePropertyValue "report"
    $result | Add-Member -NotePropertyName title -NotePropertyValue $item.title
    $result | Add-Member -NotePropertyName usage -NotePropertyValue $item.usage
    $copyResults += $result
}

$screenshotPlan = @(
    @{ target = "01_web_executive_overview.png"; tab = "Executive Overview"; purpose = "Primary landing capture for README and slides" },
    @{ target = "02_web_mexico_executive_map.png"; tab = "Mexico Executive Map"; purpose = "Map-centric showcase capture" },
    @{ target = "03_web_regional_risk_view.png"; tab = "Regional Risk View"; purpose = "Region-level inspection capture" },
    @{ target = "04_web_model_evaluation.png"; tab = "Model Evaluation"; purpose = "Metrics and evaluation evidence capture" }
)

$screenshotResults = @()
if (-not [string]::IsNullOrWhiteSpace($ScreenshotDir)) {
    $resolvedScreenshotDir = (Resolve-Path -LiteralPath $ScreenshotDir).Path
    $available = Get-ChildItem -LiteralPath $resolvedScreenshotDir -File | Sort-Object Name
    for ($i = 0; $i -lt [Math]::Min($available.Count, $screenshotPlan.Count); $i++) {
        $plan = $screenshotPlan[$i]
        $sourcePath = $available[$i].FullName
        $destinationPath = Join-Path $capturesOut $plan.target
        $result = Copy-SelectedFile -SourcePath $sourcePath -DestinationPath $destinationPath -Overwrite:$Overwrite
        $result | Add-Member -NotePropertyName category -NotePropertyValue "web_capture"
        $result | Add-Member -NotePropertyName tab -NotePropertyValue $plan.tab
        $result | Add-Member -NotePropertyName purpose -NotePropertyValue $plan.purpose
        $screenshotResults += $result
    }
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$manifestPath = Join-Path $metadataOut "presentation_assets_manifest.json"
$reportPath = Join-Path $metadataOut ("presentation_assets_report_{0}.md" -f $timestamp)

$payload = [PSCustomObject]@{
    repo_root = $repoRootPath
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    plots = $copyResults | Where-Object { $_.category -eq "plot" }
    reports = $copyResults | Where-Object { $_.category -eq "report" }
    web_captures = $screenshotResults
    screenshot_plan = $screenshotPlan
}

$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

$lines = @()
$lines += "# Presentation Assets Report"
$lines += ""
$lines += "- repo_root: `"$repoRootPath`""
$lines += "- timestamp_utc: `"$($payload.timestamp)`""
$lines += ""
$lines += "## Plot Assets"
foreach ($item in $payload.plots) {
    $lines += ("- {0} | {1} | {2}" -f $item.status, $item.destination, $item.usage)
}
$lines += ""
$lines += "## Report Assets"
foreach ($item in $payload.reports) {
    $lines += ("- {0} | {1} | {2}" -f $item.status, $item.destination, $item.usage)
}
$lines += ""
$lines += "## Screenshot Plan"
foreach ($item in $payload.screenshot_plan) {
    $lines += ("- {0} | tab: {1} | purpose: {2}" -f $item.target, $item.tab, $item.purpose)
}
if ($payload.web_captures.Count -gt 0) {
    $lines += ""
    $lines += "## Imported Web Captures"
    foreach ($item in $payload.web_captures) {
        $lines += ("- {0} | {1} | {2}" -f $item.status, $item.destination, $item.purpose)
    }
}
$lines -join [Environment]::NewLine | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Host ("[prepare_presentation_assets] manifest={0}" -f $manifestPath)
Write-Host ("[prepare_presentation_assets] report={0}" -f $reportPath)
