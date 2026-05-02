from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _window_days(window_spec: str) -> int:
    spec = str(window_spec).strip().lower()
    if not spec.endswith("d"):
        raise ValueError(f"Unsupported window_spec: {window_spec}")
    return int(spec[:-1])


def generate_sliding_windows(events: list[dict], window_spec: str, step_days: int = 7) -> list[dict]:
    if not events:
        return []

    days = _window_days(window_spec)
    dates = [_parse_dt(e["occurred_at_utc"]) for e in events if e.get("occurred_at_utc")]
    if not dates:
        return []

    start = min(dates)
    end = max(dates)

    # garantizar al menos una ventana aunque el rango sea corto
    effective_end = max(end, start + timedelta(days=days))
    cursor = start + timedelta(days=days)

    windows: list[dict] = []
    while cursor <= effective_end:
        window_start = cursor - timedelta(days=days)
        window_end = cursor

        future_start = window_end
        future_end = window_end + timedelta(days=days)

        windows.append(
            {
                "window_start_utc": window_start.isoformat(),
                "window_end_utc": window_end.isoformat(),
                "future_start_utc": future_start.isoformat(),
                "future_end_utc": future_end.isoformat(),
            }
        )
        cursor += timedelta(days=step_days)

    return windows


# compatibilidad con callers antiguos
def build_time_windows(events: list[dict], window_spec: str):
    windows = generate_sliding_windows(events, window_spec=window_spec, step_days=7)
    if not windows:
        raise ValueError("No windows could be generated.")
    first = windows[0]
    return first["window_start_utc"], first["window_end_utc"]
