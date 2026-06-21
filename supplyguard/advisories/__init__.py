"""OSV advisory models, parsing, and version primitives."""

from supplyguard.advisories.models import (
    Advisory,
    AffectedPackage,
    EventKind,
    RangeType,
    UnsupportedVersionRangeError,
    VersionEvent,
    VersionRange,
)
from supplyguard.advisories.parser import AdvisoryParseError, parse_osv, parse_osv_text
from supplyguard.advisories.versions import InvalidSemanticVersionError, SemanticVersion

__all__ = [
    "Advisory",
    "AdvisoryParseError",
    "AffectedPackage",
    "EventKind",
    "InvalidSemanticVersionError",
    "RangeType",
    "SemanticVersion",
    "UnsupportedVersionRangeError",
    "VersionEvent",
    "VersionRange",
    "parse_osv",
    "parse_osv_text",
]
