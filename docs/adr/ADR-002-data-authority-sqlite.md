# ADR-002 — Data Authority: SQLite

- Status: Accepted
- Date: 2026-04-13

## Context

A bounded local-first prototype requires a structured and legible operational authority.

Without an explicit authority decision, the repository risks fragmenting into:

- loose CSV files
- notebook-local state
- inconsistent intermediate artifacts
- ad hoc feature exports without durable structure

The current phase needs a low-cost, open-source, locally executable authority layer that is easy to inspect and sufficient for prototype discipline.

---

## Decision

SQLite is adopted as the structured prototype authority for the current phase.

Authority boundaries are:

- raw source evidence remains separate under raw data surfaces
- SQLite stores structured curated state for the prototype
- reports, plots, and model artifacts remain derived outputs

SQLite is chosen because it is:

- local-first
- open-source
- low-cost
- easy to inspect
- adequate for bounded prototype persistence

---

## Consequences

### Positive
- creates a single structured authority for the prototype
- reduces ambiguity across reruns
- improves traceability between ingestion, curation, and modeling
- avoids unnecessary operational complexity in the current phase

### Negative
- not designed for large-scale distributed production workflows
- requires intentional schema discipline
- may need future migration if scope expands significantly

---

## Implications

This decision affects:

- ingestion design
- schema management
- evidence registration
- feature provenance
- validation expectations
- documentation of authority boundaries

The repository must not treat loose derived files as authority just because they are easy to inspect.

---

## Rule

If a proposal bypasses SQLite as structured authority without a stronger architectural reason, it should be treated as regression toward ambiguity.
