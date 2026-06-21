"""Shared parser result types."""

from dataclasses import dataclass

from supplyguard.domain import SourceEvidence


@dataclass(frozen=True, order=True, slots=True)
class ParseWarning:
    """A non-fatal input issue that must remain visible to users."""

    code: str
    message: str
    evidence: SourceEvidence
