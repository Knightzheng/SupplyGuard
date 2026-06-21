"""Tests for immutable dependency domain models."""

import unittest

from supplyguard.domain import Component, DependencyEdge, Ecosystem, SourceEvidence


class SourceEvidenceTest(unittest.TestCase):
    def test_normalizes_separator_and_preserves_json_pointer(self) -> None:
        evidence = SourceEvidence("fixtures\\package-lock.json", "/packages/node_modules/a")

        self.assertEqual(evidence.source_file, "fixtures/package-lock.json")
        self.assertEqual(evidence.location, "/packages/node_modules/a")

    def test_rejects_absolute_and_traversing_paths(self) -> None:
        invalid_paths = ("C:\\private\\package-lock.json", "/private/package-lock.json", "../x")

        for path in invalid_paths:
            with self.subTest(path=path), self.assertRaises(ValueError):
                SourceEvidence(path)

    def test_rejects_non_pointer_location(self) -> None:
        with self.assertRaisesRegex(ValueError, "start with '/'"):
            SourceEvidence("package-lock.json", "packages/a")


class ComponentTest(unittest.TestCase):
    def test_builds_deterministic_scoped_npm_id(self) -> None:
        first = Component(
            Ecosystem.NPM,
            "@Example/Widget",
            "1.2.3-beta.1",
            (SourceEvidence("b.json"), SourceEvidence("a.json")),
        )
        second = Component(
            Ecosystem.NPM,
            "@example/widget",
            "1.2.3-beta.1",
            (SourceEvidence("different.json"),),
        )

        self.assertEqual(first.name, "@example/widget")
        self.assertEqual(first.id, "pkg:npm/%40example/widget@1.2.3-beta.1")
        self.assertEqual(first.id, second.id)
        self.assertEqual(
            first.evidence,
            (SourceEvidence("a.json"), SourceEvidence("b.json")),
        )

    def test_normalizes_pypi_name_using_pep_503_rules(self) -> None:
        component = Component(Ecosystem.PYPI, "Friendly_Bard...Tools", "2.0")

        self.assertEqual(component.name, "friendly-bard-tools")
        self.assertEqual(component.id, "pkg:pypi/friendly-bard-tools@2.0")

    def test_rejects_invalid_names_and_versions(self) -> None:
        invalid_components = (
            (Ecosystem.NPM, "", "1.0.0"),
            (Ecosystem.NPM, "@scope-only", "1.0.0"),
            (Ecosystem.NPM, "invalid/name", "1.0.0"),
            (Ecosystem.PYPI, "package", "  "),
        )

        for ecosystem, name, version in invalid_components:
            with self.subTest(name=name, version=version), self.assertRaises(ValueError):
                Component(ecosystem, name, version)


class DependencyEdgeTest(unittest.TestCase):
    def test_parentless_edge_is_direct(self) -> None:
        direct = DependencyEdge("pkg:npm/a@1", declared_requirement="^1")
        transitive = DependencyEdge("pkg:npm/b@1", parent_id="pkg:npm/a@1")

        self.assertTrue(direct.is_direct)
        self.assertFalse(transitive.is_direct)

    def test_rejects_blank_identifiers_and_requirements(self) -> None:
        with self.assertRaisesRegex(ValueError, "child_id"):
            DependencyEdge(" ")
        with self.assertRaisesRegex(ValueError, "parent_id"):
            DependencyEdge("pkg:npm/a@1", parent_id=" ")
        with self.assertRaisesRegex(ValueError, "declared_requirement"):
            DependencyEdge("pkg:npm/a@1", declared_requirement=" ")


if __name__ == "__main__":
    unittest.main()
