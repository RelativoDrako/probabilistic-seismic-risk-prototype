# API Contract

## Navigation

- [README](../README.md)
- [HOW_TO_READ_REPO](../HOW_TO_READ_REPO.md)
- [HOW_TO_RUN](../HOW_TO_RUN.md)
- [Architecture](./architecture.md)
- [Data Governance](./data_governance.md)
- [Model Card](./model_card.md)
- [Future Work](./future_work.md)

---

## 1. Purpose

This document defines the role and contract of the API surface inside PSRP.

It explains:

- what the API is for;
- what kinds of information it exposes;
- how it fits into the repository architecture;
- what assumptions govern its use;
- and what boundaries apply to the current implementation.

## 2. API Role in the Prototype

The API exists as a **local integration and query surface**.

Its role is to expose selected structured outputs from the prototype in a way that supports:

- inspectability;
- modularity;
- interoperability;
- controlled reuse of outputs;
- and separation between internal repository logic and external consumption.

It is **not** presented as:

- a production backend;
- a public operational service;
- a real-time warning API;
- or a continuously internet-dependent platform.

## 3. Current Boundary

The current API boundary is:

- local-first;
- read-oriented;
- suitable for local or controlled-network access;
- bounded to repository outputs and structured summaries;
- not intended for public high-scale deployment;
- not intended for real-time emergency operation;
- not dependent on continuous public internet access for core behavior.

## 4. Versioning

Canonical versioning rule:

`/api/v1/...`

## 5. API Endpoint Families

Minimum canonical endpoint families:

- `health`
- `metadata`
- `regions`
- `risk-summary`
- `model-summary`
- `artifacts`
- `reports`
- `plots`

## 6. Representative Endpoints

- `/api/v1/health`
- `/api/v1/metadata`
- `/api/v1/regions`
- `/api/v1/risk-summary`

The current implementation may still expose a smaller set of routes while the contract is being stabilized.

## 7. Read-Only / Bounded Classification

The current API should be treated as **read-oriented**.

Not part of the current claim set:

- mutation-heavy workflows;
- public write endpoints;
- operational control functions;
- institutional command surfaces;
- autonomous alerting or escalation behavior.

## 8. Example Response Shapes

### Health
```json
{
  "status": "ok",
  "surface": "api",
  "version": "v1"
}
```

### Metadata
```json
{
  "project": "Probabilistic Seismic Risk Prototype",
  "mode": "local-first",
  "boundary": "bounded",
  "api_version": "v1"
}
```

## 9. Local Deployment Assumptions

The API is currently designed for:

- local execution;
- controlled workstation environments;
- lab or prototype environments;
- controlled LAN/WAN-connected usage when required.

## 10. Relationship to the Web Surface

The web layer may consume the API as a structured data surface to support:

- cleaner separation of concerns;
- consistent retrieval of bounded outputs;
- reusable presentation logic;
- and a more inspectable executive exploration layer.

## 11. Closing Statement

The PSRP API should be read as a **bounded, read-oriented integration surface** inside a local-first flagship technical proof.
