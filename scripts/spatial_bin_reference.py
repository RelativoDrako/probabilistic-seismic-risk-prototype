from __future__ import annotations

import math

def quantize_half_degree(value: float) -> float:
    return math.floor(value / 0.5) * 0.5

def derive_spatial_bin(latitude: float, longitude: float) -> str:
    lat_bin = quantize_half_degree(latitude)
    lon_bin = quantize_half_degree(longitude)
    return f"bin_{lat_bin:.1f}_{lon_bin:.1f}"
