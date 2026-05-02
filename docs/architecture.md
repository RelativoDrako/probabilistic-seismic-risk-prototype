# Architecture

## Navigation

- [README](../README.md)
- [HOW_TO_READ_REPO](../HOW_TO_READ_REPO.md)
- [HOW_TO_RUN](../HOW_TO_RUN.md)
- [Data Governance](./data_governance.md)
- [Model Card](./model_card.md)
- [API Contract](./api_contract.md)
- [Future Work](./future_work.md)

---

## 1. Purpose

This document explains the architectural structure of the **Probabilistic Seismic Risk Prototype (PSRP)** as a bounded, local-first technical proof.

It clarifies:

- what the system is;
- how the main surfaces connect;
- where authority lives;
- how evidence flows into derived artifacts;
- and what operational boundaries define the current implementation.

---

## 2. Architectural Thesis

PSRP is designed as a **local-first prototype** for bounded probabilistic seismic context analysis, traceable evidence generation, and publication-safe engineering communication.

The architecture intentionally separates:

- raw evidence;
- structured prototype authority;
- transformation and feature generation;
- analytical / model evaluation;
- integration surfaces;
- and public-facing interpretation artifacts.

The goal is not to simulate a national operations platform. The goal is to demonstrate a disciplined system shape in which evidence, interpretation, system boundaries, and publication surfaces remain understandable and defensible.

---

## 3. Architectural Principles

- **Local-first first** — core operation is designed around local execution and local authority.
- **Evidence before claims** — derived outputs must remain linked to traceable evidence and bounded interpretation.
- **Explicit system surfaces** — API, web, reports, and model outputs are different layers with different roles.
- **Publication-safe framing** — what is visible publicly must remain technically defensible.
- **No unnecessary redesign** — architectural refinement should happen through clarification and stabilization, not folder churn.

---

## 4. Canonical System Surfaces

### 4.1 Raw Evidence Surface
Source inputs and raw evidence records preserved for provenance and reproducibility.

### 4.2 Structured Authority Surface
SQLite-backed prototype authority used for curated records, local queries, and reproducible downstream processing.

### 4.3 Processing and Feature Surface
Normalization, enrichment, aggregation, and bounded feature-generation from evidence and authority.

### 4.4 Training and Evaluation Surface
Bounded analytical stages that produce summaries, evaluation outputs, and model artifacts without making deterministic or operational claims.

### 4.5 API Surface
A **local integration and query surface** that exposes structured outputs as a bounded interface layer.

### 4.6 Web Surface
An **executive exploration surface** that presents selected maps, summaries, metrics, and evidence links.

### 4.7 Artifact Surface
Selected reports, maps, plots, summaries, and demo evidence used for publication-safe review.

---

## 5. High-Level Flow

1. source evidence is acquired and preserved;
2. curated records are structured into SQLite authority;
3. processing and feature generation derive bounded intermediate representations;
4. analytical / model stages produce evaluation outputs;
5. reports, plots, and maps are generated as inspectable artifacts;
6. API and web surfaces expose bounded access to selected outputs.

---

## 6. Data and Authority Model

The architecture depends on a clear distinction between:

- **Raw Evidence** — immutable source-oriented inputs preserved for provenance.
- **Structured Authority** — SQLite-backed curated prototype authority used for reproducible local interpretation and query.
- **Derived Artifacts** — reports, plots, maps, summaries, and structured outputs generated from the authority and bounded pipeline.

This distinction prevents the repository from collapsing into a single undifferentiated workspace.

---

## 7. Local-First Operational Boundary

The current implementation is local-first.

That means:

- core operation does not depend on continuous public internet access;
- structured authority, processing, evaluation, API inspection, and web review can operate locally;
- the system is compatible with controlled LAN/WAN-connected environments when needed;
- cloud augmentation is future work, not a current dependency.

### Acquisition boundary
Dataset acquisition may require **temporary internet connectivity** during source download.

This does not change the local-first thesis:

- source downloads can be performed from another machine;
- datasets can be transferred into the operating environment locally;
- local updates can be performed without making public internet access a core dependency.

---

## 8. API and Web in Architectural Context

### API
Architecturally, the API exists to expose bounded repository outputs as a structured integration layer.

It demonstrates:
- modularity;
- interoperability;
- controlled read-oriented access;
- separation between internal data handling and external consumption.

### Web
Architecturally, the web exists to provide a bounded review and communication layer.

It demonstrates:
- executive readability;
- explainable public presentation;
- integration of maps, metrics, and evidence;
- controlled communication of what the system does and does not claim.

Neither layer should be interpreted as a separate product line.

---

## 9. Non-Goals

The current architecture does **not** aim to provide:

- public real-time warning operations;
- deterministic forecasting;
- institutional seismic authority;
- cloud-native production deployment;
- unconstrained internet ingestion as a hard dependency;
- or a generalized national operations platform.

---

## 10. Related Documents

- `docs/data_governance.md` — source, provenance, acquisition, authority, and local update model
- `docs/model_card.md` — model purpose, outputs, limits, and misuse boundaries
- `docs/api_contract.md` — API role, endpoint families, and response examples
- `docs/future_work.md` — bounded next steps without overclaiming
- `architecture/README.md` — visual and diagrammatic support layer

---

## 11. Closing Statement

PSRP should be read as a **coherent flagship technical proof**: local-first, bounded, traceable, publication-safe, and architecturally defendable.
