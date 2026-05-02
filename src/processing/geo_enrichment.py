from __future__ import annotations


def resolve_region_code(latitude: float, longitude: float) -> str | None:
    if latitude is None or longitude is None:
        return None

    # Minimal controlled fallback for prototype regional grouping.
    if latitude >= 23.0:
        return "MX_NORTH"
    if latitude >= 18.5:
        return "MX_CENTRAL"
    return "MX_SOUTH"


def resolve_municipality_code(latitude: float, longitude: float) -> str | None:
    return None
