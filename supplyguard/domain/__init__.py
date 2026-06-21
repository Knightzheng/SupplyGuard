"""Core domain types shared by parsers, matching, and reporting."""

from supplyguard.domain.models import (
    Component,
    DependencyEdge,
    DependencyScope,
    Ecosystem,
    SourceEvidence,
)

__all__ = [
    "Component",
    "DependencyEdge",
    "DependencyScope",
    "Ecosystem",
    "SourceEvidence",
]
