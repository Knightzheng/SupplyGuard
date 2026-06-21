"""Immutable OSV advisory domain models."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from supplyguard.advisories.versions import SemanticVersion
from supplyguard.domain import Ecosystem, normalize_package_name


class UnsupportedVersionRangeError(ValueError):
    """Raised when a stored OSV range lacks a safe local comparator."""


class RangeType(StrEnum):
    """Range types defined by the OSV schema."""

    SEMVER = "SEMVER"
    ECOSYSTEM = "ECOSYSTEM"
    GIT = "GIT"


class EventKind(StrEnum):
    """Version boundary events defined by the OSV schema."""

    INTRODUCED = "introduced"
    FIXED = "fixed"
    LAST_AFFECTED = "last_affected"
    LIMIT = "limit"


@dataclass(frozen=True, slots=True)
class VersionEvent:
    """A single boundary event in an OSV affected range."""

    kind: EventKind
    version: str

    def __post_init__(self) -> None:
        kind = EventKind(self.kind)
        version = self.version.strip()
        if not version:
            raise ValueError("version event must not be empty")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "version", version)


@dataclass(frozen=True, slots=True)
class VersionRange:
    """An OSV event range with explicit endpoint semantics."""

    type: RangeType
    events: tuple[VersionEvent, ...]

    def __post_init__(self) -> None:
        range_type = RangeType(self.type)
        events = tuple(self.events)
        if not events:
            raise ValueError("version range must contain events")
        has_fixed = any(event.kind is EventKind.FIXED for event in events)
        has_last_affected = any(event.kind is EventKind.LAST_AFFECTED for event in events)
        if has_fixed and has_last_affected:
            raise ValueError("fixed and last_affected events are mutually exclusive")

        open_interval = False
        for event in events:
            if event.kind is EventKind.INTRODUCED:
                if open_interval:
                    raise ValueError("introduced event cannot start before the prior interval closes")
                open_interval = True
            elif not open_interval:
                raise ValueError(f"{event.kind.value} event requires a preceding introduced event")
            else:
                open_interval = False

        object.__setattr__(self, "type", range_type)
        object.__setattr__(self, "events", events)

    @property
    def fixed_versions(self) -> tuple[str, ...]:
        """Return fixed endpoints without treating limits as fixes."""
        return tuple(event.version for event in self.events if event.kind is EventKind.FIXED)

    def contains(self, version: str) -> bool:
        """Check SemVer membership using OSV endpoint inclusivity rules."""
        if self.type is not RangeType.SEMVER:
            raise UnsupportedVersionRangeError(
                f"local comparator is not implemented for {self.type.value} ranges"
            )
        target = SemanticVersion.parse(version)
        start: SemanticVersion | None = None

        for event in self.events:
            if event.kind is EventKind.INTRODUCED:
                start = None if event.version == "0" else SemanticVersion.parse(event.version)
                continue

            end = SemanticVersion.parse(event.version)
            starts_before_target = start is None or start <= target
            if event.kind is EventKind.LAST_AFFECTED:
                ends_after_target = target <= end
            else:
                ends_after_target = target < end
            if starts_before_target and ends_after_target:
                return True
            start = None

        if start is None:
            return False
        return start <= target


@dataclass(frozen=True, slots=True)
class AffectedPackage:
    """A supported package entry from an OSV advisory."""

    ecosystem: Ecosystem
    name: str
    ranges: tuple[VersionRange, ...] = ()
    versions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ecosystem = Ecosystem(self.ecosystem)
        object.__setattr__(self, "ecosystem", ecosystem)
        object.__setattr__(self, "name", normalize_package_name(ecosystem, self.name))
        object.__setattr__(self, "ranges", tuple(self.ranges))
        object.__setattr__(self, "versions", tuple(sorted(set(self.versions))))

    def explicitly_affects(self, version: str) -> bool:
        """Whether OSV lists this exact version in ``affected.versions``."""
        return version in self.versions


@dataclass(frozen=True, slots=True)
class Advisory:
    """The supported, deterministic subset of an OSV record."""

    id: str
    modified: datetime
    affected: tuple[AffectedPackage, ...]
    published: datetime | None = None
    aliases: tuple[str, ...] = ()
    summary: str | None = None

    def __post_init__(self) -> None:
        advisory_id = self.id.strip()
        if not advisory_id:
            raise ValueError("advisory id must not be empty")
        if self.modified.tzinfo is None:
            raise ValueError("modified timestamp must include a timezone")
        if self.published is not None and self.published.tzinfo is None:
            raise ValueError("published timestamp must include a timezone")
        object.__setattr__(self, "id", advisory_id)
        object.__setattr__(
            self,
            "affected",
            tuple(sorted(self.affected, key=lambda item: (item.ecosystem.value, item.name))),
        )
        object.__setattr__(self, "aliases", tuple(sorted(set(self.aliases))))
