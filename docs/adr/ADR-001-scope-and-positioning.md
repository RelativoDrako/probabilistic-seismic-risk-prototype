# ADR-001 — Scope and Positioning

- Status: Accepted
- Date: 2026-04-13

## Context

The repository must be positioned as a professional, defensible, local-first prototype for probabilistic regional seismic risk modeling in Mexico.

Without an explicit scope decision, the repository risks being misread as one of the following:

- a deterministic earthquake prediction system
- an official warning platform
- a production-grade cloud service
- a loose ML experiment repository without architectural discipline

The project needs a stable identity that is technically honest and professionally useful.

---

## Decision

The repository is positioned as a **bounded local-first prototype** with the following characteristics:

- open-source-only current phase
- SQLite as structured prototype authority
- raw data preserved as immutable evidence
- baseline probabilistic modeling
- lightweight API and web prototype surfaces
- portfolio-grade documentation and traceability

The repository is explicitly **not** positioned as:

- an official warning system
- a deterministic earthquake prediction system
- a production deployment
- a cloud-dependent current-phase implementation

---

## Consequences

### Positive
- reduces ambiguity about claims
- improves professional defensibility
- aligns documentation, code, and artifacts under one architectural narrative
- supports coherent public presentation of the repository

### Negative
- constrains scope expansion in the current phase
- requires explicit rejection of hype-driven framing
- may require deferring attractive but non-essential features

---

## Implications

This decision affects:

- README wording
- disclaimer language
- architecture boundaries
- model card limitations
- roadmap prioritization
- API and web surface expectations

Every public-facing artifact should reinforce the bounded prototype positioning instead of weakening it.

---

## Rule

If a proposed change makes the repository look like a deterministic predictor, operational warning service, or premature production platform, that proposal should be rejected or reframed.
