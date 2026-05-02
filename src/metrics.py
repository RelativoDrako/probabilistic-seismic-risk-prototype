"""
Basic metrics for detection:
- simple threshold-based early detection
- latency and false positive simulation
"""

import numpy as np

def threshold_detection(signal, threshold=1.0):
    """
    Detect first index where signal exceeds threshold
    """
    for idx, val in enumerate(signal):
        if val >= threshold:
            return idx
    return None

def evaluate_detection(signal, threshold=1.0, event_start=None):
    detected_idx = threshold_detection(signal, threshold)
    latency = None
    if detected_idx is not None and event_start is not None:
        latency = detected_idx - event_start
    false_positive = 0
    if detected_idx is not None and detected_idx < event_start:
        false_positive = 1
    return {"detected_idx": detected_idx, "latency": latency, "false_positive": false_positive}

if __name__ == "__main__":
    from generate_signals import generate_seismic_signal
    sig = generate_seismic_signal(length=2000, magnitude=6.0, noise_level=0.2, seed=42)
    metrics = evaluate_detection(sig, threshold=0.5, event_start=1000)
    print(metrics)
