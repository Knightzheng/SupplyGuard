"""Immutable domain models for dependency analysis."""

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from urllib.parse import quote

_PYPI_NORMALIZE_PATTERN = re.compile(r"[-_.]+")


class Ecosystem(StrEnum):
    """Package ecosystems supported by the shared domain model."""

    NPM = "npm"
    PYPI = "pypi"


class DependencyScope(StrEnum):
    """The declaration context of a dependency relationship."""

    RUNTIME = "runtime"
    DEVELOPMENT = "development"
    OPTIONAL = "optional"
    PEER = "peer"


def _required_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in normalized:
        raise ValueError(f"{field_name} must not contain null bytes")
    return normalized


def normalize_package_name(ecosystem: Ecosystem, name: str) -> str:
    """Return the canonical package name for a supported ecosystem."""
    normalized = _required_text(name, "name")
    if ecosystem is Ecosystem.NPM:
        normalized = normalized.lower()
        if normalized.startswith("@"):
            if normalized.count("/") != 1:
                raise ValueError("scoped npm names must have the form @scope/package")
            scope, package = normalized.split("/", maxsplit=1)
            if len(scope) == 1 or not package:
                raise ValueError("scoped npm names must include both scope and package")
        elif "/" in normalized:
            raise ValueError("unscoped npm names must not contain a slash")
        return normalized
    if ecosystem is Ecosystem.PYPI:
        return _PYPI_NORMALIZE_PATTERN.sub("-", normalized).lower()
    raise ValueError(f"unsupported ecosystem: {ecosystem}")


def _package_url(ecosystem: Ecosystem, name: str, version: str) -> str:
    if ecosystem is Ecosystem.NPM and name.startswith("@"):
        scope, package = name[1:].split("/", maxsplit=1)
        encoded_name = f"%40{quote(scope, safe='')}/{quote(package, safe='')}"
    else:
        encoded_name = quote(name, safe=".-_~")
    return f"pkg:{ecosystem.value}/{encoded_name}@{quote(version, safe='')}"


@dataclass(frozen=True, order=True, slots=True)
class SourceEvidence:
    """A safe, project-relative pointer to the source of an observed fact."""

    source_file: str
    location: str = ""

    def __post_init__(self) -> None:
        source_file = _required_text(self.source_file, "source_file").replace("\\", "/")
        posix_path = PurePosixPath(source_file)
        windows_path = PureWindowsPath(source_file)
        if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
            raise ValueError("source_file must be project-relative")
        if ".." in posix_path.parts:
            raise ValueError("source_file must not traverse outside the project")

        location = self.location.strip()
        if "\x00" in location:
            raise ValueError("location must not contain null bytes")
        if location and not location.startswith("/"):
            raise ValueError("location must be empty or start with '/'")

        object.__setattr__(self, "source_file", posix_path.as_posix())
        object.__setattr__(self, "location", location)


@dataclass(frozen=True, slots=True)
class Component:
    """A package identified independently from where it was observed."""

    ecosystem: Ecosystem
    name: str
    version: str
    evidence: tuple[SourceEvidence, ...] = ()

    def __post_init__(self) -> None:
        ecosystem = Ecosystem(self.ecosystem)
        name = normalize_package_name(ecosystem, self.name)
        version = _required_text(self.version, "version")
        evidence = tuple(sorted(set(self.evidence)))

        object.__setattr__(self, "ecosystem", ecosystem)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "evidence", evidence)

    @property
    def id(self) -> str:
        """Return a deterministic Package URL used as the internal component ID."""
        return _package_url(self.ecosystem, self.name, self.version)


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    """A declared relationship between a project or component and a component."""

    child_id: str
    parent_id: str | None = None
    declared_requirement: str | None = None
    evidence: SourceEvidence | None = None
    scope: DependencyScope = DependencyScope.RUNTIME

    def __post_init__(self) -> None:
        child_id = _required_text(self.child_id, "child_id")
        parent_id = None
        if self.parent_id is not None:
            parent_id = _required_text(self.parent_id, "parent_id")
        requirement = self.declared_requirement
        if requirement is not None:
            requirement = _required_text(requirement, "declared_requirement")
        scope = DependencyScope(self.scope)

        object.__setattr__(self, "child_id", child_id)
        object.__setattr__(self, "parent_id", parent_id)
        object.__setattr__(self, "declared_requirement", requirement)
        object.__setattr__(self, "scope", scope)

    @property
    def is_direct(self) -> bool:
        """Whether the edge starts at the scanned project root."""
        return self.parent_id is None
