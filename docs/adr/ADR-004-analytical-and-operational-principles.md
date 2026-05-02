# ADR-004 — Analytical and Operational Principles

## Status
Accepted

## Context

The repository needed a compact canonical place to consolidate several recurring operational and analytical principles that were previously scattered in low-density notes.

## Decision

PSRP adopts these principles:

1. **Local-first / edge-first preference**  
   Execution should prefer local or controlled-network environments before adding remote dependencies.

2. **Decision-support only**  
   Outputs are bounded analytical aids, not public warning decisions or deterministic directives.

3. **Baseline models first**  
   The prototype should establish interpretable baseline behavior before expanding into more complex model families.

4. **Generic before specialized**  
   Shared and reusable procedural logic should be preferred before asset-specific tuning.

5. **Confidence and threshold discipline**  
   Any thresholding or confidence-oriented communication must remain explicit and bounded.

6. **Rule-based plus ML under bounded use**  
   Rule-based controls and ML-oriented methods may coexist, but ML does not override interpretive or governance boundaries.

7. **Distributed deployment as future-capable pattern**  
   Broader distributed or hybrid deployment is a future-capable option, not a current requirement or claim.

## Consequences

These principles reinforce a prototype that is:

- local-first;
- bounded;
- repeatable;
- explainable;
- and publication-safe.
