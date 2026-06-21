"""Component and advisory matching services."""

from supplyguard.matching.advisories import (
    AdvisoryMatchResult,
    MatchEvidence,
    MatchMethod,
    MatchWarning,
    match_advisory,
)

__all__ = [
    "AdvisoryMatchResult",
    "MatchEvidence",
    "MatchMethod",
    "MatchWarning",
    "match_advisory",
]
