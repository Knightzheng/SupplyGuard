"""Safe parser for the supported OSV schema subset."""

import json
from datetime import datetime
from pathlib import Path

from supplyguard.advisories.models import (
    Advisory,
    AffectedPackage,
    EventKind,
    RangeType,
    VersionEvent,
    VersionRange,
)
from supplyguard.domain import Ecosystem, SourceEvidence

MAX_OSV_BYTES = 10 * 1024 * 1024


class AdvisoryParseError(ValueError):
    """Raised when an OSV record is invalid or outside the supported subset."""


def _mapping(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AdvisoryParseError(f"{location} must be a JSON object")
    return value


def _list(value: object, location: str) -> list[object]:
    if not isinstance(value, list):
        raise AdvisoryParseError(f"{location} must be a JSON array")
    return value


def _text(value: object, location: str, *, required: bool = True) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AdvisoryParseError(f"{location} must be a non-empty string")
    return value.strip()


def _timestamp(value: object, location: str, *, required: bool = True) -> datetime | None:
    text = _text(value, location, required=required)
    if text is None:
        return None
    try:
        timestamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise AdvisoryParseError(f"{location} must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None:
        raise AdvisoryParseError(f"{location} must include a timezone")
    return timestamp


def _ecosystem(value: object, location: str) -> Ecosystem:
    text = _text(value, location)
    mapping = {"npm": Ecosystem.NPM, "PyPI": Ecosystem.PYPI}
    try:
        return mapping[text]
    except KeyError as error:
        raise AdvisoryParseError(f"{location} ecosystem is not supported: {text}") from error


def _version_range(value: object, location: str) -> VersionRange:
    payload = _mapping(value, location)
    try:
        range_type = RangeType(_text(payload.get("type"), f"{location}/type"))
    except ValueError as error:
        raise AdvisoryParseError(f"{location}/type is not a valid OSV range type") from error
    raw_events = _list(payload.get("events"), f"{location}/events")
    events: list[VersionEvent] = []
    for index, raw_event in enumerate(raw_events):
        event_payload = _mapping(raw_event, f"{location}/events/{index}")
        known_keys = [kind.value for kind in EventKind if kind.value in event_payload]
        if len(known_keys) != 1 or len(event_payload) != 1:
            raise AdvisoryParseError(
                f"{location}/events/{index} must contain exactly one OSV event"
            )
        event_kind = EventKind(known_keys[0])
        event_version = _text(
            event_payload[event_kind.value],
            f"{location}/events/{index}/{event_kind.value}",
        )
        events.append(VersionEvent(event_kind, event_version))
    try:
        return VersionRange(range_type, tuple(events))
    except ValueError as error:
        raise AdvisoryParseError(f"invalid events at {location}: {error}") from error


def _affected_package(value: object, location: str) -> AffectedPackage:
    payload = _mapping(value, location)
    package = _mapping(payload.get("package"), f"{location}/package")
    ecosystem = _ecosystem(package.get("ecosystem"), f"{location}/package/ecosystem")
    name = _text(package.get("name"), f"{location}/package/name")

    raw_ranges = payload.get("ranges", [])
    ranges = tuple(
        _version_range(item, f"{location}/ranges/{index}")
        for index, item in enumerate(_list(raw_ranges, f"{location}/ranges"))
    )
    raw_versions = _list(payload.get("versions", []), f"{location}/versions")
    versions = tuple(
        _text(version, f"{location}/versions/{index}")
        for index, version in enumerate(raw_versions)
    )
    try:
        return AffectedPackage(ecosystem, name, ranges, versions)
    except ValueError as error:
        raise AdvisoryParseError(f"invalid affected package at {location}: {error}") from error


def parse_osv_text(
    content: str,
    *,
    source_file: str = "advisory.json",
    max_bytes: int = MAX_OSV_BYTES,
) -> Advisory:
    """Parse an OSV JSON record without executing or resolving package code."""
    SourceEvidence(source_file)
    if max_bytes < 1:
        raise ValueError("max_bytes must be at least 1")
    if len(content.encode("utf-8")) > max_bytes:
        raise AdvisoryParseError(f"OSV record exceeds maximum size of {max_bytes} bytes")
    try:
        payload = _mapping(json.loads(content), "OSV root")
    except json.JSONDecodeError as error:
        raise AdvisoryParseError(f"OSV record must contain valid JSON: {error.msg}") from error

    advisory_id = _text(payload.get("id"), "/id")
    modified = _timestamp(payload.get("modified"), "/modified")
    published = _timestamp(payload.get("published"), "/published", required=False)
    aliases = tuple(
        _text(alias, f"/aliases/{index}")
        for index, alias in enumerate(_list(payload.get("aliases", []), "/aliases"))
    )
    summary = _text(payload.get("summary"), "/summary", required=False)
    affected = tuple(
        _affected_package(item, f"/affected/{index}")
        for index, item in enumerate(_list(payload.get("affected", []), "/affected"))
    )
    try:
        return Advisory(advisory_id, modified, affected, published, aliases, summary)
    except ValueError as error:
        raise AdvisoryParseError(f"invalid OSV advisory: {error}") from error


def parse_osv(
    path: Path,
    *,
    source_file: str | None = None,
    max_bytes: int = MAX_OSV_BYTES,
) -> Advisory:
    """Read and parse a UTF-8 OSV JSON record with a size limit."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be at least 1")
    if path.stat().st_size > max_bytes:
        raise AdvisoryParseError(f"OSV record exceeds maximum size of {max_bytes} bytes")
    try:
        content = path.read_text(encoding="utf-8-sig")
    except UnicodeError as error:
        raise AdvisoryParseError("OSV record must be UTF-8 encoded") from error
    return parse_osv_text(
        content,
        source_file=source_file or path.name,
        max_bytes=max_bytes,
    )
