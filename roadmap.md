# Roadmap

## Current direction

This repository is being developed as a **bounded local-first prototype** for probabilistic regional seismic risk modeling in Mexico.

The roadmap prioritizes:

- architectural coherence
- traceability
- reproducible reruns
- explicit scope boundaries
- professional documentation
- low-cost implementation discipline

---

## Stage 0 — Repository positioning and canonical surface

### Objective
Establish the repository as a coherent professional prototype.

### Target outcomes
- canonical root documentation
- explicit scope and disclaimer
- ADR-backed architectural boundaries
- stable repository structure
- clear separation between evidence, authority, implementation, and presentation

### Status
Substantially established.

---

## Stage 1 — Local-first data authority

### Objective
Consolidate SQLite as the structured authority of the prototype.

### Target outcomes
- stable SQLite schema
- ingestion batch registration
- feature and run traceability
- derived artifact registration
- raw evidence preserved independently from curated authority

### Risks
- schema drift
- undocumented transforms
- loose artifact generation outside canonical surfaces

---

## Stage 2 — Bounded ingestion and curation

### Objective
Strengthen the seismic data ingestion and curation path.

### Target outcomes
- bounded source acquisition
- reproducible normalization
- explicit data quality checks
- safe reruns
- consistent curated tables for downstream feature generation

### Risks
- silent source variability
- inconsistent record normalization
- ambiguous date range expansion

---

## Stage 3 — Regional feature pipeline

### Objective
Formalize region-level analytical feature generation.

### Target outcomes
- reproducible feature definitions
- explicit feature provenance
- clear separation between raw, curated, and derived data
- defensible baseline feature set

### Risks
- feature leakage
- unstable feature semantics
- overcomplication before baseline discipline is proven

---

## Stage 4 — Baseline model and evaluation discipline

### Objective
Maintain a defensible modeling layer before adding complexity.

### Target outcomes
- simple baseline models
- transparent evaluation reports
- threshold analysis
- portfolio-grade visual and written evidence
- limitations documented alongside results

### Risks
- inflated claims
- overfitting to a bounded dataset
- confusing exploratory results with operational capability

---

## Stage 5 — API and lightweight presentation surface

### Objective
Expose prototype outputs through minimal but coherent internal surfaces.

### Target outcomes
- health and summary endpoints
- lightweight query or summary routes
- web presentation of metrics and outputs
- explicit display of limitations and non-operational status

### Risks
- over-presenting prototype surfaces as productized systems
- UI drift detached from actual artifacts
- undocumented API contracts

---

## Stage 6 — Evidence, observability, and presentation quality

### Objective
Improve traceability and professional readability.

### Target outcomes
- cleaner reports
- artifact manifests where justified
- stronger narrative consistency across root docs
- presentation assets aligned with real repository outputs

### Risks
- documentation drift
- duplicate sources of truth
- visual artifacts that outpace real implementation

---

## Stage 7 — Future expansion candidates

These are future possibilities, not current commitments.

Potential directions:

- longer historical time windows
- richer geospatial aggregation
- stronger feature engineering
- more advanced baseline comparisons
- tighter API/web integration
- optional cloud-aligned future architecture

These directions must remain subordinate to the current bounded local-first scope.

---

## Explicit non-goals for the current phase

The current phase does not aim to deliver:

- a production platform
- an official warning system
- deterministic earthquake prediction
- managed cloud dependency as a requirement
- large-scale distributed infrastructure
- institutional-grade emergency operations

---

## Success criteria for the current roadmap phase

The current roadmap phase is successful if the repository remains:

- coherent
- reproducible
- bounded
- low ambiguity
- traceable
- locally executable
- professionally defensible
