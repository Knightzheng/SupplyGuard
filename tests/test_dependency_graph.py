"""Behavioral tests for the deterministic dependency graph."""

import unittest

from supplyguard.domain import Component, DependencyEdge, Ecosystem, SourceEvidence
from supplyguard.graph import DependencyGraph, GraphValidationError


def npm_component(
    name: str,
    version: str = "1.0.0",
    *evidence: SourceEvidence,
) -> Component:
    return Component(Ecosystem.NPM, name, version, evidence)


class DependencyGraphTest(unittest.TestCase):
    def test_merges_component_evidence_and_sorts_output(self) -> None:
        a_from_second_file = npm_component("a", "1.0.0", SourceEvidence("z-lock.json"))
        a_from_first_file = npm_component("a", "1.0.0", SourceEvidence("a-lock.json"))
        b = npm_component("b")

        graph = DependencyGraph((b, a_from_second_file, a_from_first_file))

        self.assertEqual([component.name for component in graph.components], ["a", "b"])
        self.assertEqual(
            graph.components[0].evidence,
            (SourceEvidence("a-lock.json"), SourceEvidence("z-lock.json")),
        )

    def test_rejects_edges_with_missing_components(self) -> None:
        a = npm_component("a")

        with self.assertRaisesRegex(GraphValidationError, "child component"):
            DependencyGraph((a,), (DependencyEdge("pkg:npm/missing@1.0.0"),))
        with self.assertRaisesRegex(GraphValidationError, "parent component"):
            DependencyGraph((a,), (DependencyEdge(a.id, "pkg:npm/missing@1.0.0"),))

    def test_returns_deterministic_direct_and_transitive_paths(self) -> None:
        a = npm_component("a")
        b = npm_component("b")
        c = npm_component("c")
        graph = DependencyGraph(
            (c, b, a),
            (
                DependencyEdge(a.id),
                DependencyEdge(b.id),
                DependencyEdge(c.id, a.id),
                DependencyEdge(c.id, b.id),
            ),
        )

        self.assertEqual(graph.direct_dependency_ids, (a.id, b.id))
        self.assertEqual(graph.paths_to(c.id), ((a.id, c.id), (b.id, c.id)))

    def test_detects_cycles_without_looping_path_search(self) -> None:
        a = npm_component("a")
        b = npm_component("b")
        graph = DependencyGraph(
            (a, b),
            (
                DependencyEdge(a.id),
                DependencyEdge(b.id, a.id),
                DependencyEdge(a.id, b.id),
            ),
        )

        self.assertEqual(graph.cycles(), ((a.id, b.id),))
        self.assertEqual(graph.paths_to(b.id), ((a.id, b.id),))

    def test_rejects_unknown_path_target_and_invalid_limits(self) -> None:
        graph = DependencyGraph()

        with self.assertRaises(KeyError):
            graph.paths_to("pkg:npm/missing@1")
        with self.assertRaisesRegex(ValueError, "max_paths"):
            DependencyGraph((npm_component("a"),)).paths_to(
                "pkg:npm/a@1.0.0",
                max_paths=0,
            )


if __name__ == "__main__":
    unittest.main()
