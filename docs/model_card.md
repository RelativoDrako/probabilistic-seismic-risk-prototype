# Model Card

## Navigation

- [README](../README.md)
- [HOW_TO_READ_REPO](../HOW_TO_READ_REPO.md)
- [HOW_TO_RUN](../HOW_TO_RUN.md)
- [Architecture](./architecture.md)
- [Data Governance](./data_governance.md)
- [API Contract](./api_contract.md)
- [Future Work](./future_work.md)

---

## 1. Purpose

This document explains the analytical role of the model layer inside PSRP.

Its goal is to clarify:

- what the current model-oriented workflow is designed to do;
- what kinds of inputs and outputs it uses;
- how its outputs should be interpreted;
- what limits apply to the current implementation;
- and what the repository does **not** claim.

## 2. Model Role in the Prototype

The model layer supports a **bounded probabilistic interpretation workflow** over structured historical seismic evidence.

Its role is to help produce:

- regional probabilistic context;
- bounded summaries from curated evidence;
- inspectable outputs for technical review;
- publication-safe artifacts such as reports, plots, and maps.

At its current stage, the prototype should also be understood as an **early-phase data curation and interpretation environment**.

## 3. Current Analytical Framing

The current repository should be understood as operating on **historical or previously acquired evidence**.

That means the analytical layer is designed primarily for:

- review of past evidence;
- bounded contextual interpretation;
- traceable artifact generation;
- structured technical communication;
- disciplined preparation of data for future analytical expansion.

It is **not necessary to update the dataset continuously** unless the objective changes toward a more time-sensitive or near-real-time analytical scenario.

## 4. Inputs

The current analytical workflow operates over inputs derived from:

- source evidence acquired from public reference datasets;
- curated records loaded into structured local authority;
- bounded features and intermediate representations generated from that authority.

## 5. Outputs

The current analytical layer produces outputs such as:

- probabilistic regional summaries;
- selected evaluation metrics;
- model summaries;
- maps and plots;
- publication-safe reports and demo evidence artifacts.

## 6. Interpretive Boundary

Outputs should be read as:

- bounded analytical products;
- contextual and probabilistic views;
- traceable outputs derived from structured evidence;
- technical proof artifacts.

They should **not** be read as:

- deterministic predictions;
- guarantees of future seismic behavior;
- real-time public safety signals;
- institutional decisions;
- production-grade operational directives.

## 7. Why Constant Dataset Refresh Is Not Required

The repository currently analyzes **evidence from the past**, not a live operational feed.

Because of that:

- constant dataset refresh is not a core requirement of the current prototype;
- local processing and interpretation can continue once the dataset has been acquired and staged locally;
- the value of the current implementation comes from traceability, bounded analysis, repeatable procedure, and disciplined communication.

## 8. Current Technology Boundary

### Present focus
- bounded probabilistic interpretation;
- historical evidence analysis;
- traceable artifact generation;
- publication-safe outputs;
- repeatable procedural structure for future model-oriented work.

### What the prototype demonstrates today
The prototype demonstrates that the implementation is correct as a **procedural and structural baseline** for:

- curating historical datasets;
- formalizing repeatable workflows;
- organizing structured evidence;
- producing defensible reports and analytical artifacts;
- establishing a reusable base for future data science work.

### Not currently presented as core capabilities
- real-time predictive analytics;
- validated operational probabilistic forecasting;
- ML deployment as a validated operational layer;
- DL deployment as a validated operational layer;
- cloud-dependent inference or orchestration.

## 9. Evaluation View

The evaluation layer should be read as a bounded technical review surface.

Its role is to help answer questions such as:

- does the pipeline remain coherent from evidence to output?
- are outputs traceable and interpretable?
- do reports, plots, and maps support a disciplined reading of the prototype?
- does the system communicate limits clearly enough?

## 10. Known Limitations

- bounded prototype, not operational public platform;
- acquired datasets, no continuous live ingestion assumption;
- contextual and probabilistic, not deterministic;
- no validated ML/DL production behavior claimed;
- not an official warning, emergency response, or public alerting system.

## 11. Misuse Warning

This repository should not be used as:

- a source of public warning decisions;
- a deterministic forecasting engine;
- a substitute for professional seismic monitoring institutions;
- a production platform for high-stakes public safety operations.

## 12. Closing Statement

The analytical layer in PSRP should be read as a **bounded probabilistic interpretation component** inside a local-first technical proof.

Its value comes from disciplined limits, historical evidence handling, traceable outputs, repeatable procedural structure, and professional communication of what the prototype can and cannot support.
