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

$tempPy = Join-Path $reportsDir "_tmp_export_publication_data_snapshot.py"

$code = @'
import json
import math
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

repo_root = Path(sys.argv[1])
strong_threshold = float(sys.argv[2])
db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
reports_dir = repo_root / "artifacts" / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

REFERENCE_GEOGRAPHIES = [
    {"label": "Baja California / Gulf of California", "political_division": "Baja California, Baja California Sur, Sonora", "latitude": 29.5, "longitude": -114.5},
    {"label": "Sonora - Sinaloa Pacific Margin", "political_division": "Sonora, Sinaloa, Nayarit", "latitude": 26.5, "longitude": -109.8},
    {"label": "Jalisco - Colima", "political_division": "Jalisco, Colima", "latitude": 19.4, "longitude": -104.3},
    {"label": "Michoacán", "political_division": "Michoacán", "latitude": 18.8, "longitude": -101.7},
    {"label": "Guerrero", "political_division": "Guerrero", "latitude": 17.6, "longitude": -99.7},
    {"label": "Oaxaca", "political_division": "Oaxaca", "latitude": 16.7, "longitude": -96.6},
    {"label": "Chiapas", "political_division": "Chiapas", "latitude": 15.8, "longitude": -93.3},
    {"label": "Central Mexico", "political_division": "Ciudad de México, Estado de México, Morelos, Puebla", "latitude": 19.4, "longitude": -99.1},
    {"label": "Veracruz - Gulf Coast", "political_division": "Veracruz, Tabasco", "latitude": 19.2, "longitude": -96.4},
    {"label": "Yucatán Peninsula", "political_division": "Yucatán, Campeche, Quintana Roo", "latitude": 20.7, "longitude": -89.0},
]
REGION_CODE_FALLBACKS = {
    "MX_NORTH": {"label": "Northern Mexico Activity Band", "political_division": "Baja California, Sonora, Chihuahua, Coahuila"},
    "MX_CENTRAL": {"label": "Central Mexico Activity Band", "political_division": "Jalisco, Colima, Michoacán, Estado de México, Ciudad de México, Puebla"},
    "MX_SOUTH": {"label": "Southern Mexico Activity Band", "political_division": "Guerrero, Oaxaca, Chiapas"},
}

def distance_score(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def ref_geo(lat, lon, region_code=None):
    if lat is not None and lon is not None:
        nearest = min(REFERENCE_GEOGRAPHIES, key=lambda item: distance_score(lat, lon, item["latitude"], item["longitude"]))
        return {"reference_geography": nearest["label"], "political_division": nearest["political_division"]}
    if region_code in REGION_CODE_FALLBACKS:
        return {"reference_geography": REGION_CODE_FALLBACKS[region_code]["label"], "political_division": REGION_CODE_FALLBACKS[region_code]["political_division"]}
    return {"reference_geography": region_code or "Mexico prototype aggregation", "political_division": "Prototype regional aggregation in Mexico"}

def row_to_dict(row):
    return {k: row[k] for k in row.keys()}

if not db_path.exists():
    raise SystemExit(f"Missing SQLite database: {db_path}")

con = sqlite3.connect(str(db_path))
con.row_factory = sqlite3.Row

tables = {r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
if "curated_events" not in tables:
    raise SystemExit("Missing required table: curated_events")

overview_row = con.execute("""
    SELECT
        COUNT(*) AS total_events,
        MIN(occurred_at_utc) AS first_event_at_utc,
        MAX(occurred_at_utc) AS latest_event_at_utc,
        MAX(magnitude_value) AS strongest_magnitude,
        SUM(CASE WHEN magnitude_value >= ? THEN 1 ELSE 0 END) AS strong_event_count
    FROM curated_events
""", (strong_threshold,)).fetchone()

top_events = con.execute("""
    SELECT occurred_at_utc, latitude, longitude, magnitude_value, depth_km, region_code
    FROM curated_events
    ORDER BY magnitude_value DESC, occurred_at_utc DESC
    LIMIT 15
""").fetchall()

strongest_by_year = con.execute("""
    SELECT substr(occurred_at_utc, 1, 4) AS year, MAX(magnitude_value) AS max_magnitude, COUNT(*) AS event_count
    FROM curated_events
    GROUP BY substr(occurred_at_utc, 1, 4)
    ORDER BY year ASC
""").fetchall()

strong_counts_by_year = con.execute("""
    SELECT substr(occurred_at_utc, 1, 4) AS year, COUNT(*) AS strong_event_count
    FROM curated_events
    WHERE magnitude_value >= ?
    GROUP BY substr(occurred_at_utc, 1, 4)
    ORDER BY year ASC
""", (strong_threshold,)).fetchall()

monthly_all = con.execute("""
    SELECT substr(occurred_at_utc, 6, 2) AS month, COUNT(*) AS event_count
    FROM curated_events
    GROUP BY substr(occurred_at_utc, 6, 2)
    ORDER BY month ASC
""").fetchall()

monthly_strong = con.execute("""
    SELECT substr(occurred_at_utc, 6, 2) AS month, COUNT(*) AS strong_event_count
    FROM curated_events
    WHERE magnitude_value >= ?
    GROUP BY substr(occurred_at_utc, 6, 2)
    ORDER BY month ASC
""", (strong_threshold,)).fetchall()

regional = con.execute("""
    SELECT
        region_code,
        AVG(latitude) AS centroid_latitude,
        AVG(longitude) AS centroid_longitude,
        COUNT(*) AS event_count_total,
        SUM(CASE WHEN magnitude_value >= ? THEN 1 ELSE 0 END) AS strong_event_count,
        MAX(magnitude_value) AS max_magnitude,
        AVG(magnitude_value) AS mean_magnitude,
        AVG(depth_km) AS mean_depth_km
    FROM curated_events
    GROUP BY region_code
    ORDER BY event_count_total DESC
""", (strong_threshold,)).fetchall()

overview = row_to_dict(overview_row)
first_dt = datetime.strptime(overview["first_event_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
latest_dt = datetime.strptime(overview["latest_event_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
coverage_years = max((latest_dt - first_dt).days / 365.25, 0.01)
overview["coverage_years"] = round(coverage_years, 2)
overview["avg_events_per_year"] = round(overview["total_events"] / coverage_years, 2)

top_events_payload = []
for row in top_events:
    item = row_to_dict(row)
    item.update(ref_geo(item.get("latitude"), item.get("longitude"), item.get("region_code")))
    top_events_payload.append(item)

monthly_all_payload = [row_to_dict(r) for r in monthly_all]
monthly_strong_payload = [row_to_dict(r) for r in monthly_strong]
strong_by_year_payload = [row_to_dict(r) for r in strong_counts_by_year]
strongest_by_year_payload = [row_to_dict(r) for r in strongest_by_year]
regional_payload = []
for row in regional:
    item = row_to_dict(row)
    item.update(ref_geo(item.get("centroid_latitude"), item.get("centroid_longitude"), item.get("region_code")))
    regional_payload.append(item)

most_active_region = regional_payload[0] if regional_payload else None
highest_magnitude_region = sorted(regional_payload, key=lambda r: (r.get("max_magnitude") or 0), reverse=True)[0] if regional_payload else None
peak_month = max(monthly_all_payload, key=lambda r: r["event_count"]) if monthly_all_payload else None
peak_strong_month = max(monthly_strong_payload, key=lambda r: r["strong_event_count"]) if monthly_strong_payload else None
peak_strong_year = max(strong_by_year_payload, key=lambda r: r["strong_event_count"]) if strong_by_year_payload else None

descriptive_findings = [
    f"The current repository dataset covers {overview['total_events']:,} curated events between {overview['first_event_at_utc']} and {overview['latest_event_at_utc']}.",
    f"The strongest recorded event in the current dataset reaches magnitude {overview['strongest_magnitude']}.",
]
if top_events_payload:
    descriptive_findings.append(f"The strongest recorded event cluster is historically associated with {top_events_payload[0]['reference_geography']}.")
if most_active_region:
    descriptive_findings.append(f"The most historically active prototype region in the current dataset is {most_active_region['reference_geography']} with {most_active_region['event_count_total']} recorded events.")
if highest_magnitude_region:
    descriptive_findings.append(f"The region with the highest recorded regional maximum magnitude is {highest_magnitude_region['reference_geography']} with a maximum magnitude of {highest_magnitude_region['max_magnitude']}.")
if peak_month:
    descriptive_findings.append(f"Month {peak_month['month']} shows the highest total recorded activity concentration in the current dataset.")
if peak_strong_month:
    descriptive_findings.append(f"Month {peak_strong_month['month']} shows the highest concentration of strong events at or above magnitude {strong_threshold} in the current dataset.")
if peak_strong_year:
    descriptive_findings.append(f"Year {peak_strong_year['year']} contains the highest count of strong events at or above magnitude {strong_threshold} in the current dataset.")

publication_boundaries = [
    "These findings are descriptive summaries from the current repository dataset.",
    "They support prototype interpretation and publication readiness.",
    "They do not constitute official warnings or deterministic prediction claims.",
]

payload = {
    "overview": overview,
    "strongest_events": top_events_payload,
    "monthly_activity": {
        "all_events": monthly_all_payload,
        "strong_events": monthly_strong_payload,
        "strong_threshold": strong_threshold,
    },
    "yearly_strong_activity": {
        "strong_counts_by_year": strong_by_year_payload,
        "strongest_magnitude_by_year": strongest_by_year_payload,
        "strong_threshold": strong_threshold,
    },
    "regional_concentration": regional_payload,
    "descriptive_findings": descriptive_findings,
    "publication_boundaries": publication_boundaries,
}

timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
json_path = reports_dir / f"publication_data_snapshot_{timestamp}.json"
md_path = reports_dir / f"publication_data_snapshot_{timestamp}.md"
json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

lines = [
    "# Publication Data Snapshot",
    "",
    f"- total_events: {overview['total_events']}",
    f"- first_event_at_utc: `{overview['first_event_at_utc']}`",
    f"- latest_event_at_utc: `{overview['latest_event_at_utc']}`",
    f"- strongest_magnitude: `{overview['strongest_magnitude']}`",
    f"- strong_event_count_at_or_above_{strong_threshold}: `{overview['strong_event_count']}`",
    f"- coverage_years: `{overview['coverage_years']}`",
    f"- avg_events_per_year: `{overview['avg_events_per_year']}`",
    "",
    "## Descriptive Findings",
]
for item in descriptive_findings:
    lines.append(f"- {item}")
lines += ["", "## Strongest Historical Events"]
for item in top_events_payload[:10]:
    lines.append(f"- `{item['occurred_at_utc']}` | M `{item['magnitude_value']}` | {item['reference_geography']} | {item['political_division']}")
lines += ["", "## Monthly Activity"]
for item in monthly_all_payload:
    lines.append(f"- month `{item['month']}` | total_events `{item['event_count']}`")
lines += ["", "## Strong Event Counts By Month"]
for item in monthly_strong_payload:
    lines.append(f"- month `{item['month']}` | strong_events `{item['strong_event_count']}`")
lines += ["", "## Regions With Highest Historical Concentration"]
for item in regional_payload[:8]:
    lines.append(f"- {item['reference_geography']} | {item['political_division']} | total_events `{item['event_count_total']}` | strong_events `{item['strong_event_count']}` | max_magnitude `{item['max_magnitude']}`")
lines += ["", "## Publication Boundaries"]
for item in publication_boundaries:
    lines.append(f"- {item}")
md_path.write_text("\n".join(lines), encoding="utf-8")

print(f"[export_publication_data_snapshot] json={json_path}")
print(f"[export_publication_data_snapshot] markdown={md_path}")
'@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tempPy, $code, $utf8NoBom)

Push-Location $repoRootPath
try {
    & $pythonExe $tempPy $repoRootPath $StrongMagnitudeThreshold
    if ($LASTEXITCODE -ne 0) {
        throw "Snapshot export failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $tempPy) {
        Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    }
}
