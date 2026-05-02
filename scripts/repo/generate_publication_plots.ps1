[CmdletBinding()]
param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$plotsDir = Join-Path $repoRootPath "artifacts\plots"
$reportsDir = Join-Path $repoRootPath "artifacts\reports"
if (-not (Test-Path -LiteralPath $plotsDir)) {
    New-Item -ItemType Directory -Path $plotsDir -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
}

$venvPython = Join-Path $repoRootPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = Join-Path $repoRootPath "venv\Scripts\python.exe"
}
$pythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }

$tempPy = Join-Path $reportsDir "_tmp_generate_publication_plots.py"

$code = @'
import json
import sqlite3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

repo_root = Path(sys.argv[1])
plots_dir = repo_root / "artifacts" / "plots"
reports_dir = repo_root / "artifacts" / "reports"
db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
plots_dir.mkdir(parents=True, exist_ok=True)
reports_dir.mkdir(parents=True, exist_ok=True)

snapshots = sorted(reports_dir.glob("publication_data_snapshot_*.json"))
if not snapshots:
    raise SystemExit("Missing publication_data_snapshot_*.json. Run export_publication_data_snapshot.ps1 first.")

snapshot = json.loads(snapshots[-1].read_text(encoding="utf-8"))
overview = snapshot.get("overview", {})
regional = snapshot.get("regional_concentration", [])
boundaries = snapshot.get("publication_boundaries", [])
findings = snapshot.get("descriptive_findings", [])

if db_path.exists():
    con = sqlite3.connect(str(db_path))
    mags = [row[0] for row in con.execute("SELECT magnitude_value FROM curated_events WHERE magnitude_value IS NOT NULL").fetchall()]
else:
    mags = []

plt.rcParams.update({"figure.figsize": (14, 8), "axes.titlesize": 18, "axes.labelsize": 13, "xtick.labelsize": 11, "ytick.labelsize": 11})

fig, ax = plt.subplots(figsize=(14, 7))
ax.axis("off")
cards = [
    ("Curated events", str(overview.get("total_events", "—")), "Size of the current publication-ready evidence base"),
    ("Coverage years", str(overview.get("coverage_years", "—")), "Temporal breadth represented by the current dataset"),
    ("Strongest magnitude", str(overview.get("strongest_magnitude", "—")), "Highest magnitude preserved in the current persisted view"),
    ("Strong events ≥ 6.0", str(overview.get("strong_event_count", "—")), "Count of stronger events under the current descriptive threshold"),
]
positions = [(0.04, 0.55), (0.52, 0.55), (0.04, 0.14), (0.52, 0.14)]
fills = ["#e8f1ff", "#edf7ed", "#fff0e8", "#f6ecff"]
for (title, value, desc), (x, y), fill in zip(cards, positions, fills):
    ax.add_patch(plt.Rectangle((x, y), 0.40, 0.26, facecolor=fill, edgecolor="#7c8aa5", linewidth=2.0))
    ax.text(x + 0.03, y + 0.17, title, fontsize=15, fontweight="bold", color="#223047")
    ax.text(x + 0.03, y + 0.08, value, fontsize=24, fontweight="bold", color="#111827")
    ax.text(x + 0.03, y + 0.03, desc, fontsize=10.8, color="#475569")
ax.text(0.5, 0.94, "Executive Metrics Panel", ha="center", fontsize=26, fontweight="bold")
ax.text(0.5, 0.89, "Persisted indicators that orient the executive reading of the prototype", ha="center", fontsize=13, color="#475569")
fig.tight_layout()
fig.savefig(plots_dir / "metrics_panel.png", dpi=220, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(18, 8))
ax.axis("off")
steps = [
    ("Curated events", "Preserve raw evidence", 0.05, 0.58, 0.17, 0.20, "#e8f1ff"),
    ("SQLite authority", "Structure retrieval and governance", 0.28, 0.58, 0.18, 0.20, "#edf7ed"),
    ("Feature generation", "Derive bounded analytical context", 0.51, 0.58, 0.18, 0.20, "#fff0e8"),
    ("Publication artifacts", "Persist reports and visuals", 0.74, 0.58, 0.20, 0.20, "#f6ecff"),
    ("Web publication surface", "Communicate safely and clearly", 0.39, 0.16, 0.24, 0.20, "#fef3c7"),
]
for label, desc, x, y, w, h, fill in steps:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=fill, edgecolor="#334155", linewidth=2.2))
    ax.text(x + w/2, y + h*0.62, label, ha="center", va="center", fontsize=17.5, fontweight="bold", color="#0f172a")
    ax.text(x + w/2, y + h*0.28, desc, ha="center", va="center", fontsize=10.5, color="#475569")
for start, end in [((0.22, 0.68), (0.28, 0.68)), ((0.46, 0.68), (0.51, 0.68)), ((0.69, 0.68), (0.74, 0.68)), ((0.84, 0.58), (0.57, 0.36)), ((0.39, 0.58), (0.51, 0.36))]:
    ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", linewidth=2.4, color="#475569"))
ax.text(0.5, 0.94, "Prototype Traceability Pipeline", ha="center", fontsize=28, fontweight="bold")
ax.text(0.5, 0.89, "From curated evidence to publication-safe presentation through governed, local-first stages", ha="center", fontsize=14, color="#475569")
ax.text(0.5, 0.06, "Each element contributes a distinct role: evidence preservation, structured authority, bounded analytics, persisted artifacts, and interpretable delivery.", ha="center", fontsize=12.3, color="#334155")
fig.tight_layout()
fig.savefig(plots_dir / "pipeline_trace.png", dpi=220, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 7))
top_regions = regional[:10]
labels = [r.get("reference_geography", r.get("region_code", "—")) for r in top_regions]
values = [r.get("event_count_total", 0) for r in top_regions]
ax.barh(labels[::-1], values[::-1], color=plt.cm.Blues(np.linspace(0.45, 0.90, max(len(values), 1))))
ax.set_title("Regional Event Counts")
ax.set_xlabel("Recorded events")
fig.tight_layout()
fig.savefig(plots_dir / "regional_event_counts.png", dpi=200, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 6))
heat_regions = regional[:8]
matrix = np.array([[float(r.get("event_count_total", 0) or 0), float(r.get("strong_event_count", 0) or 0), float(r.get("max_magnitude", 0) or 0)] for r in heat_regions], dtype=float)
if matrix.size == 0:
    matrix = np.zeros((1, 3))
row_labels = [r.get("reference_geography", r.get("region_code", "—")) for r in heat_regions] or ["No data"]
for col in range(matrix.shape[1]):
    max_val = matrix[:, col].max()
    if max_val > 0:
        matrix[:, col] = matrix[:, col] / max_val
im = ax.imshow(matrix, aspect="auto", cmap="viridis")
ax.set_yticks(range(len(row_labels)))
ax.set_yticklabels(row_labels)
ax.set_xticks(range(3))
ax.set_xticklabels(["Total events", "Strong events", "Max magnitude"])
ax.set_title("Relative Risk Heatmap")
plt.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
fig.tight_layout()
fig.savefig(plots_dir / "risk_heatmap.png", dpi=200, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 7))
top_regions = regional[:8]
labels = [r.get("reference_geography", r.get("region_code", "—")) for r in top_regions]
scores = [float(r.get("event_count_total", 0) or 0) + 5.0 * float(r.get("strong_event_count", 0) or 0) for r in top_regions]
ax.barh(labels[::-1], scores[::-1], color=plt.cm.plasma(np.linspace(0.25, 0.95, max(len(scores), 1))))
ax.set_title("Probabilistic Regional Concentration")
ax.set_xlabel("Prototype descriptive concentration score")
fig.tight_layout()
fig.savefig(plots_dir / "probabilistic_risk_map.png", dpi=200, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 6))
if mags:
    ax.hist(mags, bins=24, edgecolor="#334155")
    ax.set_title("Magnitude Distribution")
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Recorded events")
else:
    ax.text(0.5, 0.5, "No magnitude data available", ha="center", va="center", fontsize=16)
    ax.set_axis_off()
fig.tight_layout()
fig.savefig(plots_dir / "magnitude_distribution.png", dpi=200, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(13, 7))
ax.axis("off")
ax.text(0.5, 0.93, "Model and Publication Posture Summary", ha="center", fontsize=27, fontweight="bold")
ax.text(0.5, 0.88, "Compact governance reading of the prototype's analytical and publication state", ha="center", fontsize=13, color="#475569")
blocks = [
    ("Curated events", str(overview.get("total_events", "—")), "Evidence volume currently surfaced", "#e8f1ff", 0.05, 0.57),
    ("Coverage years", str(overview.get("coverage_years", "—")), "Temporal breadth of the persisted view", "#edf7ed", 0.37, 0.57),
    ("Strongest magnitude", str(overview.get("strongest_magnitude", "—")), "Upper observed magnitude preserved", "#fff0e8", 0.69, 0.57),
]
for title, value, desc, fill, x, y in blocks:
    ax.add_patch(plt.Rectangle((x, y), 0.25, 0.18, facecolor=fill, edgecolor="#7c8aa5", linewidth=2.0))
    ax.text(x + 0.02, y + 0.12, title, fontsize=14, fontweight="bold", color="#223047")
    ax.text(x + 0.02, y + 0.05, value, fontsize=20, fontweight="bold", color="#111827")
    ax.text(x + 0.02, y + 0.01, desc, fontsize=9.8, color="#475569")
ax.text(0.06, 0.35, "Publication boundaries", fontsize=15, fontweight="bold", color="#0f172a")
for i, line in enumerate(boundaries[:3]):
    ax.text(0.07, 0.28 - i * 0.07, f"• {line}", fontsize=12.0, color="#334155")
finding_line = findings[0] if findings else "Descriptive findings are drawn only from persisted repository evidence."
ax.text(0.06, 0.07, finding_line, fontsize=11.3, color="#334155")
fig.tight_layout()
fig.savefig(plots_dir / "model_summary_panel.png", dpi=220, bbox_inches="tight")
plt.close(fig)

print(f"[generate_publication_plots] plots_dir={plots_dir}")
'@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tempPy, $code, $utf8NoBom)

Push-Location $repoRootPath
try {
    & $pythonExe $tempPy $repoRootPath
    if ($LASTEXITCODE -ne 0) {
        throw "Plot generation failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $tempPy) {
        Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    }
}
