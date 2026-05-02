"""
Generate synthetic seismic signals for testing.
- Allows variable noise and magnitude.
- Outputs CSV for raw data storage.
"""

import numpy as np
import pandas as pd

def generate_seismic_signal(length=1000, magnitude=5.0, noise_level=0.1, seed=None):
    """
    Generate a 1D seismic signal with a main event and noise.
    """
    if seed is not None:
        np.random.seed(seed)
    # baseline noise
    signal = np.random.normal(0, noise_level, length)
    # simulate earthquake event in the middle
    event_start = length // 2
    event = magnitude * np.exp(-0.01 * np.arange(length - event_start))
    signal[event_start:] += event
    return signal

def save_signal(signal, filename="data/raw/seismic_signal.csv"):
    df = pd.DataFrame({"amplitude": signal})
    df.to_csv(filename, index=False)
    print(f"Signal saved to {filename}")

if __name__ == "__main__":
    sig = generate_seismic_signal(length=2000, magnitude=6.0, noise_level=0.2, seed=42)
    save_signal(sig)
