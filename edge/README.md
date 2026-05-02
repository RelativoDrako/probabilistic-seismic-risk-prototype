# Edge and Local Execution

## Purpose

This folder documents the practical execution posture of PSRP in local or controlled environments.

## Minimal execution target

Suitable for bounded review and light demonstration:

- modern workstation or laptop;
- CPU-only path;
- local disk available;
- enough memory for local dataset handling and surface stack execution.

## Recommended execution target

Suitable for repeatable local review and artifact generation:

- multi-core workstation or laptop;
- comfortable local storage for datasets, SQLite authority, plots, and reports;
- enough memory to run processing, evaluation, API, and web inspection without unnecessary contention.

## Ideal execution target

Suitable for richer local experimentation and broader artifact generation:

- stronger workstation-class hardware;
- more local storage for larger historical datasets;
- comfortable margin for expanded evaluation or future model experimentation.

## Current restrictions

- the prototype operates on historical or previously acquired evidence;
- constant public internet connectivity is not required after acquisition;
- dataset download may require temporary connectivity;
- no cloud dependence is required in the current baseline;
- no real-time public warning behavior is implied.

## Benefits of local-first execution

- lower dependency surface;
- stronger privacy and locality;
- repeatable review path;
- bounded analysis in controlled environments;
- easier portability across constrained operational contexts.

## SNN note

An attempt to mature an SNN-oriented acquisition path did not become the current public baseline because of practical availability, continuity, and operational-access constraints.

For publication-safe prototyping and reproducible public review, **USGS** currently serves as the primary public reference source.

## Future work

Potential future work may include:

- distributed local execution;
- cloud-agnostic augmentation where justified;
- optional offline-first dataset logistics modules;
- model-oriented expansion after stronger data maturity.
