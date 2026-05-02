# Source Code Overview

This directory contains the core pipeline logic of the project.

## Modules

- `generate_signals.py`
  Simulates seismic-like signals under controlled conditions.

- `preprocessing.py`
  Signal normalization, filtering, and feature extraction.

- `train_baseline.py`
  Trains lightweight baseline models (Logistic Regression).

- `evaluate_baseline.py`
  Evaluates models using latency, robustness, and error cost metrics.

## Design Notes

- CPU-only compatible
- Low-latency focused
- Modular for edge deployment
