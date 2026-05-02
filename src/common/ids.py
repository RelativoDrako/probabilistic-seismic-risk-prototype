from __future__ import annotations

"""
Deterministic ID compatibility layer.

This module accepts both positional arguments and keyword arguments in order
to stabilize runtime contracts across ingestion, processing, features,
training, evaluation, and visualization.
"""

import hashlib
from typing import Iterable


def _normalize_parts(parts: Iterable[object]) -> list[str]:
    normalized: list[str] = []
    for p in parts:
        if p is None:
            continue
        s = str(p).strip()
        if not s:
            continue
        normalized.append(s)
    return normalized


def _collect_parts(args: tuple[object, ...], kwargs: dict) -> tuple[object, ...]:
    if args:
        return args
    # preserve insertion order of kwargs to stay deterministic for callers
    return tuple(kwargs.values())


def build_prefixed_id(prefix: str, *parts: object, length: int = 16) -> str:
    normalized = _normalize_parts(parts)
    material = "|".join(normalized).encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()[:length]
    return f"{prefix}_{digest}"


def _build_prefixed_id(prefix: str, *parts: object, length: int = 16) -> str:
    return build_prefixed_id(prefix, *parts, length=length)


def build_ingest_batch_id(*args, **kwargs) -> str:
    return build_prefixed_id("ingest", *_collect_parts(args, kwargs))


def build_event_id(*args, **kwargs) -> str:
    return build_prefixed_id("event", *_collect_parts(args, kwargs))


def build_feature_generation_id(*args, **kwargs) -> str:
    return build_prefixed_id("featgen", *_collect_parts(args, kwargs))


def build_feature_row_id(*args, **kwargs) -> str:
    return build_prefixed_id("featrow", *_collect_parts(args, kwargs))


def build_pipeline_run_id(*args, **kwargs) -> str:
    return build_prefixed_id("run", *_collect_parts(args, kwargs))


def build_raw_asset_id(*args, **kwargs) -> str:
    return build_prefixed_id("raw", *_collect_parts(args, kwargs))


__all__ = [
    "build_prefixed_id",
    "_build_prefixed_id",
    "build_ingest_batch_id",
    "build_event_id",
    "build_feature_generation_id",
    "build_feature_row_id",
    "build_pipeline_run_id",
    "build_raw_asset_id",
]
