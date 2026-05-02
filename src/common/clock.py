from __future__ import annotations

from datetime import datetime, timezone


UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def utc_now_iso() -> str:
    return utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_utc(value: object) -> str:
    if value is None:
        raise ValueError("UTC value is required")
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(seconds, tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            raise ValueError("UTC string is empty")
        if candidate.isdigit():
            return normalize_utc(int(candidate))
        normalized = candidate.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        parsed = parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")
    raise TypeError(f"Unsupported UTC value type: {type(value)!r}")
