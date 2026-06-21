"""Parser for exact-pinned Python requirements files."""

import re
from dataclasses import dataclass
from pathlib import Path

from supplyguard.domain import Component, DependencyEdge, Ecosystem, SourceEvidence
from supplyguard.graph import DependencyGraph
from supplyguard.parsers.models import ParseWarning

MAX_REQUIREMENTS_BYTES = 5 * 1024 * 1024

_EXACT_PIN = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"(?:\[(?P<extras>[^\]]+)\])?\s*==(?!=)\s*"
    r"(?P<version>[^\s;]+)\s*(?:;\s*(?P<marker>.+))?$"
)
_INLINE_COMMENT = re.compile(r"\s+#.*$")
_HASH_OPTION = re.compile(r"\s+--hash=\S+")
_VERSION_OPERATOR = re.compile(r"(?:===|~=|!=|<=|>=|<|>)")


class RequirementsError(ValueError):
    """Raised when a requirements file cannot be parsed safely."""


@dataclass(frozen=True, slots=True)
class RequirementsResult:
    """A flattened dependency graph plus explicit parser warnings."""

    graph: DependencyGraph
    warnings: tuple[ParseWarning, ...]


def _logical_lines(content: str) -> tuple[tuple[int, str], ...]:
    logical_lines: list[tuple[int, str]] = []
    buffer = ""
    start_line = 0
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        stripped = raw_line.strip()
        if not buffer and (not stripped or stripped.startswith("#")):
            continue
        if not buffer:
            start_line = line_number
        continued = stripped.endswith("\\")
        fragment = stripped[:-1].rstrip() if continued else stripped
        buffer = f"{buffer} {fragment}".strip()
        if not continued:
            logical_lines.append((start_line, buffer))
            buffer = ""
    if buffer:
        logical_lines.append((start_line, buffer))
    return tuple(logical_lines)


def _line_evidence(source_file: str, line_number: int) -> SourceEvidence:
    return SourceEvidence(source_file, f"/lines/{line_number}")


def parse_requirements_text(
    content: str,
    *,
    source_file: str = "requirements.txt",
    max_bytes: int = MAX_REQUIREMENTS_BYTES,
) -> RequirementsResult:
    """Parse exact ``name==version`` pins without resolving or installing packages."""
    SourceEvidence(source_file)
    if max_bytes < 1:
        raise ValueError("max_bytes must be at least 1")
    if len(content.encode("utf-8")) > max_bytes:
        raise RequirementsError(f"requirements file exceeds maximum size of {max_bytes} bytes")

    components: list[Component] = []
    edges: list[DependencyEdge] = []
    warnings: list[ParseWarning] = []

    for line_number, original_line in _logical_lines(content):
        evidence = _line_evidence(source_file, line_number)
        line = _INLINE_COMMENT.sub("", original_line).strip()
        line = _HASH_OPTION.sub("", line).strip()
        if not line:
            continue

        if line.startswith("-"):
            warnings.append(
                ParseWarning(
                    "unsupported-directive",
                    f"requirements directive is not evaluated: {line.split()[0]}",
                    evidence,
                )
            )
            continue

        match = _EXACT_PIN.fullmatch(line)
        if match is None:
            code = "unpinned-requirement" if _VERSION_OPERATOR.search(line) else "unsupported-requirement"
            warnings.append(
                ParseWarning(
                    code,
                    f"requirement is not an exact supported pin: {line}",
                    evidence,
                )
            )
            continue

        name = match.group("name")
        version = match.group("version")
        marker = match.group("marker")
        if "*" in version:
            warnings.append(
                ParseWarning(
                    "unpinned-requirement",
                    f"requirement uses a wildcard version: {line}",
                    evidence,
                )
            )
            continue
        try:
            component = Component(Ecosystem.PYPI, name, version, (evidence,))
        except ValueError as error:
            raise RequirementsError(f"invalid requirement on line {line_number}: {error}") from error
        components.append(component)
        edges.append(
            DependencyEdge(
                component.id,
                declared_requirement=f"=={version}",
                evidence=evidence,
            )
        )

        if marker:
            warnings.append(
                ParseWarning(
                    "environment-marker-not-evaluated",
                    f"environment marker is preserved but not evaluated: {marker.strip()}",
                    evidence,
                )
            )

    return RequirementsResult(
        DependencyGraph(tuple(components), tuple(edges)),
        tuple(sorted(set(warnings))),
    )


def parse_requirements(
    path: Path,
    *,
    source_file: str | None = None,
    max_bytes: int = MAX_REQUIREMENTS_BYTES,
) -> RequirementsResult:
    """Read and parse a requirements file with a strict size limit."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be at least 1")
    if path.stat().st_size > max_bytes:
        raise RequirementsError(f"requirements file exceeds maximum size of {max_bytes} bytes")
    try:
        content = path.read_text(encoding="utf-8-sig")
    except UnicodeError as error:
        raise RequirementsError("requirements file must be UTF-8 encoded") from error
    return parse_requirements_text(
        content,
        source_file=source_file or path.name,
        max_bytes=max_bytes,
    )
