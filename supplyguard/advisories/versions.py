"""Version comparison primitives used by advisory ranges."""

import re
from dataclasses import dataclass
from functools import total_ordering

_SEMVER_PATTERN = re.compile(
    r"^(?:v)?(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


class InvalidSemanticVersionError(ValueError):
    """Raised when a version does not conform to SemVer 2.0 syntax."""


@total_ordering
@dataclass(frozen=True, slots=True)
class SemanticVersion:
    """A minimal, dependency-free SemVer 2.0 value object."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str) -> "SemanticVersion":
        match = _SEMVER_PATTERN.fullmatch(value.strip())
        if match is None:
            raise InvalidSemanticVersionError(f"invalid semantic version: {value!r}")
        prerelease_text = match.group("prerelease")
        prerelease = tuple(prerelease_text.split(".")) if prerelease_text else ()
        for identifier in prerelease:
            if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
                raise InvalidSemanticVersionError(
                    f"numeric prerelease identifiers must not contain leading zeroes: {value!r}"
                )
        return cls(
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch")),
            prerelease,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        own_release = (self.major, self.minor, self.patch)
        other_release = (other.major, other.minor, other.patch)
        if own_release != other_release:
            return own_release < other_release
        if self.prerelease == other.prerelease:
            return False
        if not self.prerelease:
            return False
        if not other.prerelease:
            return True

        for own_identifier, other_identifier in zip(self.prerelease, other.prerelease):
            if own_identifier == other_identifier:
                continue
            own_numeric = own_identifier.isdigit()
            other_numeric = other_identifier.isdigit()
            if own_numeric and other_numeric:
                return int(own_identifier) < int(other_identifier)
            if own_numeric != other_numeric:
                return own_numeric
            return own_identifier < other_identifier
        return len(self.prerelease) < len(other.prerelease)
