# HOW_TO_READ_REPO

## Purpose

This guide explains how to review PSRP without getting lost in implementation details.

Use it to decide whether you want an executive reading, a technical reading, a runnable demo validation, or a publication-readiness review.

---

## 1. Executive review path - 5 minutes

Read in this order:

1. [`README.md`](README.md)
2. [`demo/controlled_run/README.md`](demo/controlled_run/README.md)
3. [`demo/controlled_run/visual_review_index.html`](demo/controlled_run/visual_review_index.html)
4. [`docs/model_card.md`](docs/model_card.md)

This path explains what the prototype is, what it demonstrates, what it does not claim, and how the public surface should be interpreted.

---

## 2. Runnable surface validation path

Use this path when you want to confirm that the local API and web surface still work.

1. Open [`HOW_TO_RUN.md`](HOW_TO_RUN.md).
2. Install dependencies from the repository root.
3. Start the API and web surface.
4. Open the local web URL.
5. Inspect these sections in order:
   - Executive Overview
   - Mexico Executive Map
   - Regional Risk View
   - Model Evaluation
   - Methodology and Traceability
   - API & Integration Surface
   - Future Projection
6. Open the controlled review storyboard:
   - [`demo/controlled_run/visual_review_index.html`](demo/controlled_run/visual_review_index.html)

---

## 3. Technical architecture path

Read in this order:

1. [`docs/architecture.md`](docs/architecture.md)
2. [`docs/data_governance.md`](docs/data_governance.md)
3. [`docs/model_card.md`](docs/model_card.md)
4. [`docs/api_contract.md`](docs/api_contract.md)
5. [`docs/future_work.md`](docs/future_work.md)
6. [`docs/adr/`](docs/adr/)

This path is intended for engineering review: boundaries, authority model, traceability, local-first posture, API surface, and future expansion.

---

## 4. Evidence and artifact path

Start with:

- `artifacts/reports/demo_evidence.md`
- `artifacts/reports/evaluation_summary.md`
- `artifacts/reports/class_balance_audit.md`
- `artifacts/plots/`
- `artifacts/sqlite/seismic_prototype.db`
- `demo/controlled_run/visual_review_index.html`

The controlled demo should be treated as the public reading path. The broader artifact tree is supporting evidence and may be more technical.

---

## 5. Publication-readiness checklist

A public reviewer should be able to confirm the following quickly:

- the project is clearly local-first;
- SQLite is the structured prototype authority;
- raw evidence and derived outputs are separated;
- no absolute workstation paths are visible;
- claims remain bounded and non-deterministic;
- the web surface is readable without needing private context;
- future cloud/ML work is described as projection, not current production capability.
