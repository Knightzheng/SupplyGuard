"""Tests for safe package-lock v2/v3 dependency parsing."""

import json
import tempfile
import unittest
from pathlib import Path

from supplyguard.domain import DependencyScope
from supplyguard.parsers.package_lock import (
    PackageLockError,
    parse_package_lock,
    parse_package_lock_text,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def lockfile(payload: dict[str, object]) -> str:
    return json.dumps(payload, separators=(",", ":"))


class PackageLockParserTest(unittest.TestCase):
    def test_parses_v3_direct_nested_scoped_and_development_dependencies(self) -> None:
        content = lockfile(
            {
                "name": "demo",
                "version": "1.0.0",
                "lockfileVersion": 3,
                "packages": {
                    "": {
                        "name": "demo",
                        "version": "1.0.0",
                        "dependencies": {"alpha": "^1", "@scope/tool": "2.x"},
                        "devDependencies": {"dev-only": "^3"},
                    },
                    "node_modules/alpha": {
                        "version": "1.1.0",
                        "dependencies": {"shared": "^2"},
                    },
                    "node_modules/alpha/node_modules/shared": {"version": "2.4.0"},
                    "node_modules/@scope/tool": {
                        "version": "2.0.0",
                        "dependencies": {"shared": "^1"},
                    },
                    "node_modules/shared": {"version": "1.9.0"},
                    "node_modules/dev-only": {"version": "3.2.1", "dev": True},
                },
            }
        )

        result = parse_package_lock_text(content)
        components = {component.name: component for component in result.graph.components}
        alpha = components["alpha"]
        scoped = components["@scope/tool"]
        dev_only = components["dev-only"]
        shared_v1 = next(
            component
            for component in result.graph.components
            if component.name == "shared" and component.version == "1.9.0"
        )
        shared_v2 = next(
            component
            for component in result.graph.components
            if component.name == "shared" and component.version == "2.4.0"
        )

        self.assertEqual(result.project_name, "demo")
        self.assertEqual(result.project_version, "1.0.0")
        self.assertEqual(result.lockfile_version, 3)
        self.assertEqual(len(result.graph.components), 5)
        self.assertEqual(result.warnings, ())
        self.assertIn(alpha.id, result.graph.direct_dependency_ids)
        self.assertIn(scoped.id, result.graph.direct_dependency_ids)
        self.assertIn(dev_only.id, result.graph.direct_dependency_ids)
        self.assertEqual(result.graph.paths_to(shared_v2.id), ((alpha.id, shared_v2.id),))
        self.assertEqual(result.graph.paths_to(shared_v1.id), ((scoped.id, shared_v1.id),))
        dev_edge = next(edge for edge in result.graph.edges if edge.child_id == dev_only.id)
        self.assertEqual(dev_edge.scope, DependencyScope.DEVELOPMENT)

    def test_parses_v2_and_resolves_workspace_link_metadata(self) -> None:
        content = lockfile(
            {
                "name": "workspace-root",
                "lockfileVersion": 2,
                "packages": {
                    "": {"dependencies": {"workspace-a": "file:packages/a"}},
                    "node_modules/workspace-a": {"resolved": "packages/a", "link": True},
                    "packages/a": {
                        "name": "workspace-a",
                        "version": "1.5.0",
                        "dependencies": {"leaf": "^1"},
                    },
                    "node_modules/leaf": {"version": "1.1.0"},
                },
            }
        )

        result = parse_package_lock_text(content, source_file="fixtures/package-lock.json")
        workspace = next(component for component in result.graph.components if component.name == "workspace-a")
        leaf = next(component for component in result.graph.components if component.name == "leaf")

        self.assertEqual(result.lockfile_version, 2)
        self.assertEqual(result.graph.paths_to(leaf.id), ((workspace.id, leaf.id),))
        self.assertEqual(
            {evidence.source_file for evidence in workspace.evidence},
            {"fixtures/package-lock.json"},
        )

    def test_merges_duplicate_component_occurrence_evidence(self) -> None:
        content = lockfile(
            {
                "name": "duplicates",
                "lockfileVersion": 3,
                "packages": {
                    "": {"dependencies": {"a": "1", "b": "1"}},
                    "node_modules/a": {
                        "version": "1.0.0",
                        "dependencies": {"shared": "1"},
                    },
                    "node_modules/b": {
                        "version": "1.0.0",
                        "dependencies": {"shared": "1"},
                    },
                    "node_modules/a/node_modules/shared": {"version": "1.0.0"},
                    "node_modules/b/node_modules/shared": {"version": "1.0.0"},
                },
            }
        )

        result = parse_package_lock_text(content)
        shared = next(component for component in result.graph.components if component.name == "shared")

        self.assertEqual(len(shared.evidence), 2)
        self.assertEqual(len(result.graph.paths_to(shared.id)), 2)

    def test_reports_missing_versions_and_unresolved_dependencies(self) -> None:
        content = lockfile(
            {
                "name": "broken",
                "lockfileVersion": 3,
                "packages": {
                    "": {"dependencies": {"missing": "^1"}},
                    "node_modules/missing": {},
                },
            }
        )

        result = parse_package_lock_text(content)

        self.assertEqual(result.graph.components, ())
        self.assertEqual(
            {warning.code for warning in result.warnings},
            {"missing-version", "unresolved-dependency"},
        )

    def test_rejects_invalid_json_versions_structures_and_large_input(self) -> None:
        invalid_cases = (
            ("not-json", "valid JSON"),
            (lockfile({"lockfileVersion": 1, "packages": {}}), "version 2 or 3"),
            (lockfile({"lockfileVersion": 3, "packages": []}), "packages.*object"),
            (
                lockfile(
                    {
                        "lockfileVersion": 3,
                        "packages": {"": {"dependencies": ["not", "an", "object"]}},
                    }
                ),
                "dependencies.*object",
            ),
        )

        for content, expected_error in invalid_cases:
            with self.subTest(expected_error=expected_error), self.assertRaisesRegex(
                PackageLockError, expected_error
            ):
                parse_package_lock_text(content)

        with self.assertRaisesRegex(PackageLockError, "maximum size"):
            parse_package_lock_text("{}", max_bytes=1)

    def test_rejects_unsafe_source_file(self) -> None:
        with self.assertRaisesRegex(ValueError, "project-relative"):
            parse_package_lock_text(
                lockfile({"lockfileVersion": 3, "packages": {}}),
                source_file="C:\\private\\package-lock.json",
            )

    def test_reads_utf8_file_and_rejects_invalid_encoding(self) -> None:
        temporary_root = PROJECT_ROOT / ".tmp"
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            valid_path = Path(directory) / "package-lock.json"
            valid_path.write_text(
                lockfile({"name": "disk", "lockfileVersion": 3, "packages": {}}),
                encoding="utf-8",
            )
            invalid_path = Path(directory) / "invalid-package-lock.json"
            invalid_path.write_bytes(b"\xff\xfe\x00")

            result = parse_package_lock(valid_path)

            self.assertEqual(result.project_name, "disk")
            with self.assertRaisesRegex(PackageLockError, "UTF-8"):
                parse_package_lock(invalid_path)


if __name__ == "__main__":
    unittest.main()
