"""Validated and deterministic dependency graph implementation."""

from collections import defaultdict
from dataclasses import dataclass

from supplyguard.domain import Component, DependencyEdge


class GraphValidationError(ValueError):
    """Raised when dependency graph references are internally inconsistent."""


def _merge_components(components: tuple[Component, ...]) -> tuple[Component, ...]:
    merged: dict[str, Component] = {}
    for component in components:
        existing = merged.get(component.id)
        if existing is None:
            merged[component.id] = component
            continue
        merged[component.id] = Component(
            component.ecosystem,
            component.name,
            component.version,
            existing.evidence + component.evidence,
        )
    return tuple(merged[component_id] for component_id in sorted(merged))


def _edge_sort_key(edge: DependencyEdge) -> tuple[str, str, str, str, str]:
    evidence_file = edge.evidence.source_file if edge.evidence else ""
    evidence_location = edge.evidence.location if edge.evidence else ""
    return (
        edge.parent_id or "",
        edge.child_id,
        edge.declared_requirement or "",
        evidence_file,
        evidence_location,
    )


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    """An immutable dependency graph whose root is represented by ``None``."""

    components: tuple[Component, ...] = ()
    edges: tuple[DependencyEdge, ...] = ()

    def __post_init__(self) -> None:
        components = _merge_components(tuple(self.components))
        component_ids = {component.id for component in components}
        edges = tuple(sorted(set(self.edges), key=_edge_sort_key))

        for edge in edges:
            if edge.child_id not in component_ids:
                raise GraphValidationError(f"edge references missing child component: {edge.child_id}")
            if edge.parent_id is not None and edge.parent_id not in component_ids:
                raise GraphValidationError(
                    f"edge references missing parent component: {edge.parent_id}"
                )

        object.__setattr__(self, "components", components)
        object.__setattr__(self, "edges", edges)

    @property
    def direct_dependency_ids(self) -> tuple[str, ...]:
        """Return sorted component IDs declared directly by the project."""
        return tuple(sorted({edge.child_id for edge in self.edges if edge.is_direct}))

    def component(self, component_id: str) -> Component:
        """Return a component by stable ID."""
        for component in self.components:
            if component.id == component_id:
                return component
        raise KeyError(component_id)

    def paths_to(
        self,
        component_id: str,
        *,
        max_paths: int = 20,
        max_depth: int = 100,
    ) -> tuple[tuple[str, ...], ...]:
        """Return deterministic root-to-component paths without traversing cycles."""
        self.component(component_id)
        if max_paths < 1:
            raise ValueError("max_paths must be at least 1")
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")

        parents: dict[str, set[str | None]] = defaultdict(set)
        for edge in self.edges:
            parents[edge.child_id].add(edge.parent_id)

        results: set[tuple[str, ...]] = set()

        def visit(current: str, reverse_path: tuple[str, ...]) -> None:
            if len(results) >= max_paths or len(reverse_path) > max_depth:
                return
            for parent in sorted(parents.get(current, set()), key=lambda value: value or ""):
                if parent is None:
                    results.add(tuple(reversed(reverse_path)))
                elif parent not in reverse_path:
                    visit(parent, reverse_path + (parent,))

        visit(component_id, (component_id,))
        return tuple(sorted(results)[:max_paths])

    def cycles(self) -> tuple[tuple[str, ...], ...]:
        """Return cyclic strongly connected components in deterministic order."""
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges:
            if edge.parent_id is not None:
                adjacency[edge.parent_id].add(edge.child_id)

        index = 0
        indexes: dict[str, int] = {}
        low_links: dict[str, int] = {}
        stack: list[str] = []
        on_stack: set[str] = set()
        cyclic_components: list[tuple[str, ...]] = []

        def strong_connect(node: str) -> None:
            nonlocal index
            indexes[node] = index
            low_links[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)

            for child in sorted(adjacency.get(node, set())):
                if child not in indexes:
                    strong_connect(child)
                    low_links[node] = min(low_links[node], low_links[child])
                elif child in on_stack:
                    low_links[node] = min(low_links[node], indexes[child])

            if low_links[node] != indexes[node]:
                return

            connected: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                connected.append(member)
                if member == node:
                    break

            connected_tuple = tuple(sorted(connected))
            has_self_loop = len(connected_tuple) == 1 and node in adjacency.get(node, set())
            if len(connected_tuple) > 1 or has_self_loop:
                cyclic_components.append(connected_tuple)

        for component in self.components:
            if component.id not in indexes:
                strong_connect(component.id)

        return tuple(sorted(cyclic_components))
