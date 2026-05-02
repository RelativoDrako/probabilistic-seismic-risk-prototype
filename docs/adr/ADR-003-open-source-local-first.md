# ADR-003 — Open Source and Local-First Baseline

- Status: Accepted
- Date: 2026-04-13

## Context

The repository is intended to remain low-cost, inspectable, reproducible, and professionally defensible in its current phase.

A cloud-heavy or proprietary-first baseline would introduce unnecessary friction, hidden cost, and reduced portability for a bounded prototype.

The project needs a baseline that supports:

- local execution
- transparent tooling
- repeatable setup
- low operational burden
- future expandability without present dependency

---

## Decision

The current phase is established as:

- open-source-only by default
- local-first by default
- zero mandatory operating cost
- cloud-compatible only as future projection, not as present requirement

Implementation choices should prefer tools and workflows that can run locally with transparent behavior and low ambiguity.

---

## Consequences

### Positive
- improves accessibility and repeatability
- keeps operational cost near zero
- strengthens portability and inspection
- aligns with bounded prototype discipline

### Negative
- may delay integration of managed services
- may require more explicit local setup guidance
- limits use of convenient proprietary shortcuts in the current phase

---

## Implications

This decision affects:

- dependency selection
- runtime assumptions
- setup documentation
- pipeline orchestration
- data handling strategy
- presentation of future architecture

Cloud-oriented evolution may be documented, but it must remain clearly separated from the current implementation baseline.

---

## Rule

If a proposed change makes proprietary or cloud-managed services mandatory for the current prototype to function, that proposal should be rejected or deferred unless the project scope is explicitly re-approved.
