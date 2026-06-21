"""Explainable matching between normalized components and OSV advisories."""

from dataclasses import dataclass
from enum import StrEnum

from supplyguard.advisories import (
    Advisory,
    InvalidSemanticVersionError,
    RangeType,
    UnsupportedVersionRangeError,
)
from supplyguard.domain import Component, Ecosystem


class MatchMethod(StrEnum):
    """Evidence source that established a component match."""

    EXPLICIT_VERSION = "explicit-version"
    SEMVER_RANGE = "semver-range"


@dataclass(frozen=True, slots=True)
class MatchEvidence:
    """A reproducible reason why a component is affected."""

    advisory_id: str
    component_id: str
    method: MatchMethod
    fixed_versions: tuple[str, ...] = ()
    range_index: int | None = None


@dataclass(frozen=True, slots=True)
class MatchWarning:
    """A matching limitation that must be surfaced to callers."""

    code: str
    message: str
    advisory_id: str
    component_id: str
    range_index: int


@dataclass(frozen=True, slots=True)
class AdvisoryMatchResult:
    """Matches and explicit skipped-range warnings for one component."""

    matches: tuple[MatchEvidence, ...] = ()
    warnings: tuple[MatchWarning, ...] = ()

    @property
    def affected(self) -> bool:
        """Whether at least one supported evidence source matched."""
        return bool(self.matches)


def _evidence_key(evidence: MatchEvidence) -> tuple[str, int, tuple[str, ...]]:
    return (
        evidence.method.value,
        evidence.range_index if evidence.range_index is not None else -1,
        evidence.fixed_versions,
    )


def _warning_key(warning: MatchWarning) -> tuple[int, str, str]:
    return (warning.range_index, warning.code, warning.message)


def match_advisory(advisory: Advisory, component: Component) -> AdvisoryMatchResult:
    """Match one component without hiding unsupported version semantics."""
    matches: list[MatchEvidence] = []
    warnings: list[MatchWarning] = []

    for affected in advisory.affected:
        if affected.ecosystem is not component.ecosystem or affected.name != component.name:
            continue

        if affected.explicitly_affects(component.version):
            matches.append(
                MatchEvidence(
                    advisory.id,
                    component.id,
                    MatchMethod.EXPLICIT_VERSION,
                )
            )

        for range_index, version_range in enumerate(affected.ranges):
            if version_range.type is not RangeType.SEMVER or component.ecosystem is not Ecosystem.NPM:
                warnings.append(
                    MatchWarning(
                        "unsupported-version-range",
                        (
                            f"{version_range.type.value} comparison is not implemented "
                            f"for {component.ecosystem.value}"
                        ),
                        advisory.id,
                        component.id,
                        range_index,
                    )
                )
                continue
            try:
                is_affected = version_range.contains(component.version)
            except (InvalidSemanticVersionError, UnsupportedVersionRangeError) as error:
                warnings.append(
                    MatchWarning(
                        "invalid-or-unsupported-version",
                        str(error),
                        advisory.id,
                        component.id,
                        range_index,
                    )
                )
                continue
            if is_affected:
                matches.append(
                    MatchEvidence(
                        advisory.id,
                        component.id,
                        MatchMethod.SEMVER_RANGE,
                        version_range.fixed_versions,
                        range_index,
                    )
                )

    return AdvisoryMatchResult(
        tuple(sorted(set(matches), key=_evidence_key)),
        tuple(sorted(set(warnings), key=_warning_key)),
    )
