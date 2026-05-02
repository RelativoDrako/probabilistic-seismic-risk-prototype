"""
Preprocess seismic signals for model ingestion.
- Normalization
- Sliding window features
"""

import pandas as pd
import numpy as np

def load_signal(filename="data/raw/seismic_signal.csv"):
    df = pd.read_csv(filename)
    return df["amplitude"].values

def normalize_signal(signal):
    return (signal - np.mean(signal)) / np.std(signal)

def sliding_window(signal, window_size=50, step=10):
    """
    Generate overlapping windows
    """
    windows = []
    for start in range(0, len(signal) - window_size + 1, step):
        windows.append(signal[start:start+window_size])
    return np.array(windows)

if __name__ == "__main__":
    from generate_signals import generate_seismic_signal, save_signal
    # example pipeline
    sig = generate_seismic_signal(length=2000, magnitude=6.0, noise_level=0.2, seed=42)
    save_signal(sig)
    sig = load_signal()
    sig_norm = normalize_signal(sig)
    windows = sliding_window(sig_norm)
    print(f"Generated {len(windows)} windows from signal")
