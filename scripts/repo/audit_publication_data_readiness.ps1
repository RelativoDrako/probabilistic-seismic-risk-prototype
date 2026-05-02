[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [double]$StrongMagnitudeThreshold = 6.0
)

$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$reportsDir = Join-Path $repoRootPath "artifacts\reports"
if (-not (Test-Path -LiteralPath $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
}

$venvPython = Join-Path $repoRootPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = Join-Path $repoRootPath "venv\Scripts\python.exe"
}
$pythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }

$tempPy = Join-Path $reportsDir "_tmp_audit_publication_data_readiness.py"

$code = @'
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

repo_root = Path(sys.argv[1])
strong_threshold = float(sys.argv[2])
db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
reports_dir = repo_root / "artifacts" / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

def finding(area, status, evidence, action, blocking=False):
    return {
        "area": area,
        "status": status,
        "evidence": evidence,
        "action": action,
        "blocking": blocking,
    }

findings = []

if not db_path.exists():
    findings.append(finding("SQLite database", "blocking", f"Missing database: {db_path}", "Restore or generate the SQLite authority before publication.", True))
else:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    tables = {r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    if "curated_events" not in tables:
        findings.append(finding("curated_events", "blocking", "Missing required table: curated_events", "Populate the curated event authority before publication.", True))
    else:
        count_row = con.execute("SELECT COUNT(*) AS total_events, COUNT(DISTINCT region_code) AS distinct_regions FROM curated_events").fetchone()
        total_events = count_row["total_events"]
        distinct_regions = count_row["distinct_regions"]
        if total_events <= 0:
            findings.append(finding("curated_events population", "blocking", "curated_events contains no rows.", "Populate curated_events before publication.", True))
        else:
            findings.append(finding("curated_events population", "confirmed", f"curated_events contains {total_events} rows across {distinct_regions} distinct regions.", "Preserve current historical coverage."))
        if distinct_regions < 3:
            findings.append(finding("regional coverage", "blocking", f"Only {distinct_regions} distinct regions found.", "Increase or repair regional coverage before publication.", True))
        else:
            findings.append(finding("regional coverage", "confirmed", f"{distinct_regions} distinct regions support regional publication views.", "Keep current regional aggregation coverage."))

        strong_count = con.execute("SELECT COUNT(*) AS strong_event_count FROM curated_events WHERE magnitude_value >= ?", (strong_threshold,)).fetchone()["strong_event_count"]
        if strong_count <= 0:
            findings.append(finding("strong historical events", "blocking", f"No events at or above magnitude {strong_threshold} were found.", "Lower the threshold or restore strong-event records for the historical section.", True))
        else:
            findings.append(finding("strong historical events", "confirmed", f"{strong_count} events at or above magnitude {strong_threshold} support the historical major-event section.", "Keep current strong-event threshold or justify any change."))

        month_count = con.execute("SELECT COUNT(DISTINCT substr(occurred_at_utc, 6, 2)) AS month_count FROM curated_events").fetchone()["month_count"]
        if month_count < 6:
            findings.append(finding("monthly descriptive coverage", "partial", f"Only {month_count} months are represented in the current dataset.", "Use restrained language for monthly concentration claims.", False))
        else:
            findings.append(finding("monthly descriptive coverage", "confirmed", f"{month_count} months are represented, supporting descriptive monthly concentration analysis.", "Keep monthly activity section bounded and descriptive."))

        year_count = con.execute("SELECT COUNT(DISTINCT substr(occurred_at_utc, 1, 4)) AS year_count FROM curated_events").fetchone()["year_count"]
        if year_count < 3:
            findings.append(finding("yearly descriptive coverage", "partial", f"Only {year_count} distinct years are represented.", "Keep yearly periodicity language conservative.", False))
        else:
            findings.append(finding("yearly descriptive coverage", "confirmed", f"{year_count} distinct years support descriptive time-distribution summaries.", "Keep yearly summaries descriptive rather than predictive."))

    if "region_features" not in tables:
        findings.append(finding("region_features", "partial", "region_features is missing.", "Regional publication can fall back to curated-event aggregations, but region_features should remain preferred.", False))
    else:
        rows = con.execute("SELECT COUNT(*) AS row_count FROM region_features").fetchone()["row_count"]
        if rows <= 0:
            findings.append(finding("region_features", "partial", "region_features exists but contains no rows.", "Regenerate region_features if richer regional metrics are needed.", False))
        else:
            findings.append(finding("region_features", "confirmed", f"region_features contains {rows} rows.", "Use region_features where richer per-region metrics are required."))

    if "evaluation_reports" not in tables:
        findings.append(finding("evaluation_reports", "partial", "evaluation_reports table is missing.", "Model Evaluation must use an explicit fallback state in publication.", False))
    else:
        eval_count = con.execute("SELECT COUNT(*) AS eval_count FROM evaluation_reports").fetchone()["eval_count"]
        if eval_count <= 0:
            findings.append(finding("evaluation_reports", "partial", "evaluation_reports contains no rows.", "Model Evaluation must use an explicit fallback state in publication.", False))
        else:
            findings.append(finding("evaluation_reports", "confirmed", f"evaluation_reports contains {eval_count} rows.", "Audit live evaluation payload before final publication."))

blocking_count = sum(1 for item in findings if item["blocking"])
warning_count = sum(1 for item in findings if (not item["blocking"] and item["status"] != "confirmed"))
overall = "BLOCKED" if blocking_count > 0 else "READY_FOR_NEXT_STAGE"

timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
json_path = reports_dir / f"publication_data_readiness_{timestamp}.json"
md_path = reports_dir / f"publication_data_readiness_{timestamp}.md"

payload = {
    "repo_root": str(repo_root),
    "timestamp_utc": datetime.now(UTC).isoformat(),
    "overall_status": overall,
    "blocking_count": blocking_count,
    "warning_count": warning_count,
    "strong_threshold": strong_threshold,
    "findings": findings,
}

json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

lines = [
    "# Publication Data Readiness",
    "",
    f"- overall_status: `{overall}`",
    f"- blocking_count: {blocking_count}",
    f"- warning_count: {warning_count}",
    f"- strong_threshold: {strong_threshold}",
    "",
    "## Findings",
]
for item in findings:
    lines.append(f"- **{item['area']}** | status={item['status']} | blocking={item['blocking']}")
    lines.append(f"  - evidence: {item['evidence']}")
    lines.append(f"  - action: {item['action']}")
md_path.write_text("\n".join(lines), encoding="utf-8")

print(f"[audit_publication_data_readiness] json={json_path}")
print(f"[audit_publication_data_readiness] markdown={md_path}")
print(f"[audit_publication_data_readiness] overall={overall}")
'@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tempPy, $code, $utf8NoBom)

Push-Location $repoRootPath
try {
    & $pythonExe $tempPy $repoRootPath $StrongMagnitudeThreshold
    if ($LASTEXITCODE -ne 0) {
        throw "Data readiness audit failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $tempPy) {
        Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    }
}
