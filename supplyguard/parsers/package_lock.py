"""Safe parser for npm package-lock versions 2 and 3."""

import json
from dataclasses import dataclass
from pathlib import Path

from supplyguard.domain import (
    Component,
    DependencyEdge,
    DependencyScope,
    Ecosystem,
    SourceEvidence,
)
from supplyguard.graph import DependencyGraph

MAX_LOCKFILE_BYTES = 20 * 1024 * 1024

_DEPENDENCY_FIELDS = (
    ("dependencies", DependencyScope.RUNTIME),
    ("devDependencies", DependencyScope.DEVELOPMENT),
    ("peerDependencies", DependencyScope.PEER),
    ("optionalDependencies", DependencyScope.OPTIONAL),
)


class PackageLockError(ValueError):
    """Raised when a package-lock file cannot be parsed safely."""


@dataclass(frozen=True, order=True, slots=True)
class ParseWarning:
    """A non-fatal package-lock issue that must remain visible to users."""

    code: str
    message: str
    evidence: SourceEvidence


@dataclass(frozen=True, slots=True)
class PackageLockResult:
    """Project metadata, graph, and explicit parser warnings."""

    project_name: str
    project_version: str | None
    lockfile_version: int
    graph: DependencyGraph
    warnings: tuple[ParseWarning, ...]


@dataclass(frozen=True, slots=True)
class _Occurrence:
    component: Component
    metadata: dict[str, object]
    metadata_location: str


def _json_pointer(*tokens: object) -> str:
    escaped = (str(token).replace("~", "~0").replace("/", "~1") for token in tokens)
    return "/" + "/".join(escaped)


def _evidence(source_file: str, *tokens: object) -> SourceEvidence:
    return SourceEvidence(source_file, _json_pointer(*tokens))


def _package_name_from_location(location: str) -> str | None:
    parts = location.split("/")
    node_module_indexes = [index for index, part in enumerate(parts) if part == "node_modules"]
    if not node_module_indexes:
        return None
    index = node_module_indexes[-1] + 1
    if index >= len(parts):
        return None
    first = parts[index]
    if first.startswith("@"):
        if index + 1 >= len(parts):
            return None
        return f"{first}/{parts[index + 1]}"
    return first


def _resolution_candidates(parent_location: str, dependency_name: str) -> tuple[str, ...]:
    candidates: list[str] = []
    ancestor = parent_location
    while True:
        prefix = f"{ancestor}/" if ancestor else ""
        candidates.append(f"{prefix}node_modules/{dependency_name}")
        if not ancestor:
            break
        parts = ancestor.split("/")
        indexes = [index for index, part in enumerate(parts) if part == "node_modules"]
        if not indexes:
            ancestor = ""
        else:
            ancestor = "/".join(parts[: indexes[-1]])
    return tuple(dict.fromkeys(candidates))


def _required_mapping(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PackageLockError(f"{location} must be a JSON object")
    return value


def _optional_text(value: object, location: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise PackageLockError(f"{location} must be a non-empty string")
    return value.strip()


def _dependency_declarations(
    metadata: dict[str, object],
    *,
    source_file: str,
    package_location: str,
    metadata_location: str,
) -> tuple[tuple[str, str, DependencyScope, SourceEvidence], ...]:
    declarations: dict[str, tuple[str, DependencyScope, SourceEvidence]] = {}
    for field, scope in _DEPENDENCY_FIELDS:
        raw_dependencies = metadata.get(field)
        if raw_dependencies is None:
            continue
        dependencies = _required_mapping(
            raw_dependencies,
            _json_pointer("packages", metadata_location, field),
        )
        for dependency_name, raw_requirement in dependencies.items():
            if not isinstance(dependency_name, str) or not dependency_name.strip():
                raise PackageLockError(
                    f"{_json_pointer('packages', metadata_location, field)} has an invalid name"
                )
            requirement = _optional_text(
                raw_requirement,
                _json_pointer("packages", metadata_location, field, dependency_name),
            )
            if requirement is None:
                raise PackageLockError("dependency requirements must not be null")
            declarations[dependency_name] = (
                requirement,
                scope,
                _evidence(source_file, "packages", package_location, field, dependency_name),
            )
    return tuple(
        (name, requirement, scope, evidence)
        for name, (requirement, scope, evidence) in sorted(declarations.items())
    )


def _resolve_occurrence(
    occurrences: dict[str, _Occurrence],
    parent_location: str,
    dependency_name: str,
) -> _Occurrence | None:
    for candidate in _resolution_candidates(parent_location, dependency_name):
        occurrence = occurrences.get(candidate)
        if occurrence is not None:
            return occurrence
    return None


def parse_package_lock_text(
    content: str,
    *,
    source_file: str = "package-lock.json",
    max_bytes: int = MAX_LOCKFILE_BYTES,
) -> PackageLockResult:
    """Parse package-lock JSON without executing any project code."""
    SourceEvidence(source_file)
    if max_bytes < 1:
        raise ValueError("max_bytes must be at least 1")
    if len(content.encode("utf-8")) > max_bytes:
        raise PackageLockError(f"package-lock exceeds maximum size of {max_bytes} bytes")

    try:
        payload = json.loads(content)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise PackageLockError(f"package-lock must contain valid JSON: {error.msg}") from error
    root = _required_mapping(payload, "package-lock root")

    lockfile_version = root.get("lockfileVersion")
    if isinstance(lockfile_version, bool) or lockfile_version not in (2, 3):
        raise PackageLockError("package-lock must use lockfile version 2 or 3")

    packages = _required_mapping(root.get("packages"), "package-lock packages")
    root_metadata = _required_mapping(packages.get("", {}), _json_pointer("packages", ""))
    warnings: list[ParseWarning] = []

    project_name = _optional_text(root_metadata.get("name"), "/packages//name")
    if project_name is None:
        project_name = _optional_text(root.get("name"), "/name")
    if project_name is None:
        project_name = "unnamed-project"
        warnings.append(
            ParseWarning(
                "missing-project-name",
                "package-lock does not declare a project name",
                SourceEvidence(source_file),
            )
        )

    project_version = _optional_text(root_metadata.get("version"), "/packages//version")
    if project_version is None:
        project_version = _optional_text(root.get("version"), "/version")

    link_targets = {
        metadata.get("resolved")
        for metadata in packages.values()
        if isinstance(metadata, dict)
        and metadata.get("link") is True
        and isinstance(metadata.get("resolved"), str)
    }
    occurrences: dict[str, _Occurrence] = {}

    for raw_location, raw_metadata in sorted(packages.items()):
        if raw_location == "":
            continue
        if not isinstance(raw_location, str):
            raise PackageLockError("package locations must be strings")
        location = raw_location.replace("\\", "/").strip("/")
        metadata = _required_mapping(raw_metadata, _json_pointer("packages", raw_location))
        package_name = _package_name_from_location(location)
        if package_name is None:
            if raw_location not in link_targets:
                warnings.append(
                    ParseWarning(
                        "unsupported-package-location",
                        f"cannot derive npm package name from location: {raw_location}",
                        _evidence(source_file, "packages", raw_location),
                    )
                )
            continue

        metadata_location = raw_location
        component_evidence = [_evidence(source_file, "packages", raw_location)]
        if metadata.get("link") is True:
            resolved = metadata.get("resolved")
            if not isinstance(resolved, str) or resolved not in packages:
                warnings.append(
                    ParseWarning(
                        "unresolved-link",
                        f"workspace link target is unavailable: {resolved!r}",
                        _evidence(source_file, "packages", raw_location),
                    )
                )
                continue
            metadata_location = resolved
            metadata = _required_mapping(
                packages[resolved],
                _json_pointer("packages", resolved),
            )
            component_evidence.append(_evidence(source_file, "packages", resolved))

        metadata_name = metadata.get("name")
        if metadata_name is not None:
            package_name = _optional_text(
                metadata_name,
                _json_pointer("packages", metadata_location, "name"),
            ) or package_name
        version = _optional_text(
            metadata.get("version"),
            _json_pointer("packages", metadata_location, "version"),
        )
        if version is None:
            warnings.append(
                ParseWarning(
                    "missing-version",
                    f"package at {raw_location} has no exact version",
                    _evidence(source_file, "packages", raw_location),
                )
            )
            continue

        try:
            component = Component(
                Ecosystem.NPM,
                package_name,
                version,
                tuple(component_evidence),
            )
        except ValueError as error:
            raise PackageLockError(f"invalid component at {raw_location}: {error}") from error
        occurrences[location] = _Occurrence(component, metadata, metadata_location)

    edges: list[DependencyEdge] = []

    def add_edges(
        parent_location: str,
        parent_id: str | None,
        metadata: dict[str, object],
        metadata_location: str,
    ) -> None:
        for dependency_name, requirement, scope, evidence in _dependency_declarations(
            metadata,
            source_file=source_file,
            package_location=parent_location,
            metadata_location=metadata_location,
        ):
            occurrence = _resolve_occurrence(occurrences, parent_location, dependency_name)
            if occurrence is None:
                warnings.append(
                    ParseWarning(
                        "unresolved-dependency",
                        f"cannot resolve {dependency_name!r} from {parent_location or '<root>'}",
                        evidence,
                    )
                )
                continue
            edges.append(
                DependencyEdge(
                    occurrence.component.id,
                    parent_id,
                    requirement,
                    evidence,
                    scope,
                )
            )

    add_edges("", None, root_metadata, "")
    for location, occurrence in sorted(occurrences.items()):
        add_edges(
            location,
            occurrence.component.id,
            occurrence.metadata,
            occurrence.metadata_location,
        )

    graph = DependencyGraph(
        tuple(occurrence.component for occurrence in occurrences.values()),
        tuple(edges),
    )
    return PackageLockResult(
        project_name,
        project_version,
        lockfile_version,
        graph,
        tuple(sorted(set(warnings))),
    )


def parse_package_lock(
    path: Path,
    *,
    source_file: str | None = None,
    max_bytes: int = MAX_LOCKFILE_BYTES,
) -> PackageLockResult:
    """Read and parse a package-lock file with a strict size limit."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be at least 1")
    if path.stat().st_size > max_bytes:
        raise PackageLockError(f"package-lock exceeds maximum size of {max_bytes} bytes")
    try:
        content = path.read_text(encoding="utf-8-sig")
    except UnicodeError as error:
        raise PackageLockError("package-lock must be UTF-8 encoded") from error
    return parse_package_lock_text(
        content,
        source_file=source_file or path.name,
        max_bytes=max_bytes,
    )
