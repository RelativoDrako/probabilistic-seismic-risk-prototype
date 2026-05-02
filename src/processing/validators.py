from __future__ import annotations

from src.processing.models import CandidateEvent, ValidationIssue


def validate_candidate_event(event: CandidateEvent) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not event.occurred_at_utc:
        issues.append(ValidationIssue("timestamp_missing", "timestamp missing or invalid", "error"))

    if event.latitude is None or event.longitude is None:
        issues.append(ValidationIssue("coordinates_invalid", "latitude/longitude missing or invalid", "error"))

    if event.region_code is None:
        issues.append(ValidationIssue("region_missing", "region_code unresolved", "error"))

    if event.depth_km is None:
        issues.append(ValidationIssue("depth_missing", "depth missing or invalid", "warning"))

    if event.magnitude_value is None:
        issues.append(ValidationIssue("magnitude_missing", "magnitude missing or invalid", "warning"))

    return issues


def is_accept_event(issues: list[ValidationIssue]) -> bool:
    return all(issue.severity != "error" for issue in issues)
