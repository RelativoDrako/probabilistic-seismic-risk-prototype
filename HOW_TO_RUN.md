# HOW_TO_RUN

## Purpose

This guide explains how to install dependencies, start the local API/web surface, and validate that PSRP is ready for controlled publication review.

The current phase is local-first. The stack is intended to run locally or on a controlled LAN/WAN environment, not as a public warning service.

---

## 1. Environment baseline

Recommended:

- Windows 10/11
- PowerShell 5+ or PowerShell 7+
- Python 3.11+
- local working copy of the repository

Optional but useful:

- modern browser
- Git
- local virtual environment

---

## 2. Install dependencies

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-surface.txt
```

If the repository helper script is available, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\repo\install_surface_dependencies.ps1 -RepoRoot . -UpgradePip
```

---

## 3. Start the presentation stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\repo\start_presentation_stack.ps1 -RepoRoot . -StartApi -StartWeb
```

Expected local addresses:

- API: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- Web: `http://127.0.0.1:8501`

---

## 4. Smoke test

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\repo\smoke_test_surface_stack.ps1 -ApiBaseUrl http://127.0.0.1:8000 -WebBaseUrl http://127.0.0.1:8501
```

Expected result:

- API reachable
- summary endpoint reachable
- evaluation endpoint reachable
- web reachable
- no immediate launch failure

---

## 5. Required visual validation

Open `http://127.0.0.1:8501`.

### Sidebar

Confirm:

- `Maintained by` shows only `Daniel Franco`;
- `Authority DB` shows:
  - `seismic_prototype.db`
  - `SQLite structured authority`
  - `PSRP/artifacts/sqlite/seismic_prototype.db`
- no absolute local workstation path is visible.

### Executive Overview

Confirm:

- KPI cards are populated and readable;
- `What this prototype demonstrates` is clear;
- `What this prototype does not claim` is visible;
- only the priority visual evidence is promoted in the overview.

### Mexico Executive Map

Confirm:

- the executive map loads;
- recorded-event and tectonic-context maps are available;
- map notes are interpretive and bounded;
- the detail panel gives fast regional context.

### Regional Risk View

Confirm:

- selected region loads;
- long values wrap cleanly;
- event count, strong events, magnitude values, and Executive Risk Index are visible;
- the selected-region summary table preserves complete labels.

### Model Evaluation

Confirm:

- metric cards do not collide;
- publication-limited states are explicit;
- ROC, PR, and probability histogram views include captions;
- the section reads as bounded, not incomplete.

### Methodology and Traceability

Confirm:

- publication components are readable;
- plot inventory and report inventory are compact;
- persisted data support explains state rather than exposing raw payloads.

### API & Integration Surface

Confirm:

- endpoint chips are visible;
- the API is framed as read-oriented, local-first, and bounded;
- it does not imply production backend maturity.

### Future Projection

Confirm:

- future work is sober and optional;
- cloud and advanced ML appear as projection, not current dependency;
- the roadmap table remains readable.

---

## 6. Controlled review

After validating the live surface, open:

```text
demo/controlled_run/visual_review_index.html
```

Confirm that the storyboard:

- uses real screenshots;
- follows the same section order as the site;
- separates executive map, recorded events, and tectonic context;
- keeps captions short and useful;
- does not use premium mockups or artificial claims.

---

## 7. Interpretation boundary

PSRP remains a bounded technical proof.

It should not be interpreted as:

- an official warning system;
- deterministic earthquake prediction;
- a production deployment;
- authoritative geophysical mapping;
- a cloud-dependent service in the current phase.
