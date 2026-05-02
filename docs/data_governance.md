# Data Governance

## Navigation

- [README](../README.md)
- [HOW_TO_READ_REPO](../HOW_TO_READ_REPO.md)
- [HOW_TO_RUN](../HOW_TO_RUN.md)
- [Architecture](./architecture.md)
- [Model Card](./model_card.md)
- [API Contract](./api_contract.md)
- [Future Work](./future_work.md)

---

## 1. Purpose

This document explains how PSRP handles dataset sources, evidence classes, provenance, structured authority, local update behavior, and interpretive boundaries related to data usage.

## 2. Governance Thesis

PSRP follows an **evidence-first** and **local-first** governance model.

This means:

- source evidence must remain traceable;
- curated records must be distinguishable from raw evidence;
- derived artifacts must be reproducible from structured authority;
- publication surfaces must remain bounded and defensible;
- no claim should exceed what the evidence and prototype architecture can support.

## 3. Evidence Classes

### Raw Evidence
Source-oriented inputs acquired from external or upstream data sources.

### Structured Authority
Curated prototype records organized into SQLite.

### Derived Artifacts
Reports, plots, maps, summaries, metrics panels, and bounded outputs produced from structured authority.

## 4. Dataset Source Model

### Current public reference source
The current prototype uses **USGS** as a primary public reference source for dataset acquisition.

### Why USGS is used
USGS is used because it provides a professionally relevant and broadly recognized public reference suitable for:

- bounded prototype evidence acquisition;
- reproducible public review;
- engineering communication with familiar external references;
- traceable acquisition-to-artifact workflows.

### SNN attempt and decision path
A prior attempt to work against **SNN-oriented data usage** did not become the current public baseline due to practical availability, continuity, and operational-access constraints. Using USGS preserves public reviewability and continuity without overstating institutional coupling.

## 5. Acquisition Model

### Temporary connectivity requirement
Dataset acquisition may require **temporary internet connectivity** during source download.

### Local-first interpretation
The repository remains local-first because:

- core execution does not depend on continuous public internet access;
- datasets can be downloaded from another machine;
- datasets can be transferred into the target operating environment;
- local processing, authority generation, evaluation, API inspection, web review, and artifact generation can continue without persistent internet connectivity.

## 6. Local Dataset Update Model

A dedicated public-facing offline dataset-ingestion artifact is **not yet part of the canonical visible module set**.

At present, datasets may be refreshed through this pattern:

1. acquire source data from a connected machine;
2. transfer the dataset into the local operating environment;
3. load or update the local repository data path;
4. regenerate structured authority and derived artifacts as needed.

A dedicated offline-first dataset update module may be derived from an existing ingestion path with limited modifications.

## 7. Provenance and Traceability

The repository is designed so that a reviewer can distinguish:

- where source evidence came from;
- where structured prototype authority begins;
- and where derived interpretive outputs are generated.

Traceability should remain visible across the chain:

**source acquisition -> raw evidence -> structured authority -> derived outputs -> public artifacts**

## 8. Structured Authority Role

SQLite is used as the **structured prototype authority**.

Its purpose is to:

- stabilize local queries;
- support reproducible downstream processing;
- centralize curated structured records;
- reduce ambiguity between raw evidence and interpreted outputs.

## 9. Publication-Safe Data Behavior

Public-facing reading should prioritize:

- canonical documentation;
- selected stable reports;
- selected stable maps and plots;
- structured and interpretable outputs.

It should avoid letting these dominate the public reading path:

- repair bundles;
- cleanup residue;
- debugging artifacts;
- redundant snapshots;
- transient fix notes without durable narrative value.

## 10. Interpretive Boundaries

The presence of structured evidence and public reference datasets does **not** imply:

- official operational authority;
- deterministic forecasting;
- real-time public safety function;
- or production deployment.

## 11. Closing Statement

PSRP uses a governance model in which source evidence is traceable, structured authority is explicit, local execution remains primary, and public communication remains bounded.
