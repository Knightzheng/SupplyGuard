"""Core domain types shared by parsers, matching, and reporting."""

from supplyguard.domain.models import (
    Component,
    DependencyEdge,
    DependencyScope,
    Ecosystem,
    SourceEvidence,
    normalize_package_name,
)

__all__ = [
    "Component",
    "DependencyEdge",
    "DependencyScope",
    "Ecosystem",
    "SourceEvidence",
    "normalize_package_name",
]
