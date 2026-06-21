"""Tests for exact-pinned Python requirements parsing."""

import tempfile
import unittest
from pathlib import Path

from supplyguard.parsers.requirements import (
    RequirementsError,
    parse_requirements,
    parse_requirements_text,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RequirementsParserTest(unittest.TestCase):
    def test_parses_exact_pins_extras_hashes_and_comments(self) -> None:
        content = """
        # Reproducible application dependencies
        Requests[security]==2.32.4  # HTTP client
        friendly_bard.tools==1.0.0 \\
            --hash=sha256:aaaaaaaa \\
            --hash=sha256:bbbbbbbb
        """

        result = parse_requirements_text(content)
        components = {component.name: component for component in result.graph.components}

        self.assertEqual(set(components), {"requests", "friendly-bard-tools"})
        self.assertEqual(components["requests"].version, "2.32.4")
        self.assertEqual(len(result.graph.direct_dependency_ids), 2)
        self.assertEqual(result.warnings, ())

    def test_merges_duplicate_pins_and_preserves_line_evidence(self) -> None:
        result = parse_requirements_text("demo==1.0\nDemo==1.0\n")
        component = result.graph.components[0]

        self.assertEqual(len(result.graph.components), 1)
        self.assertEqual(
            {evidence.location for evidence in component.evidence},
            {"/lines/1", "/lines/2"},
        )

    def test_preserves_but_does_not_evaluate_environment_markers(self) -> None:
        result = parse_requirements_text('colorama==0.4.6 ; python_version < "3.13"')

        self.assertEqual(len(result.graph.components), 1)
        self.assertEqual(
            {warning.code for warning in result.warnings},
            {"environment-marker-not-evaluated"},
        )

    def test_warns_and_skips_unpinned_urls_directives_and_invalid_lines(self) -> None:
        content = """
        flask>=3
        wildcard==1.*
        package @ https://example.invalid/package.whl
        -r other.txt
        --index-url https://example.invalid/simple
        this is not valid
        """

        result = parse_requirements_text(content)

        self.assertEqual(result.graph.components, ())
        self.assertEqual(
            {warning.code for warning in result.warnings},
            {"unsupported-directive", "unsupported-requirement", "unpinned-requirement"},
        )

    def test_rejects_large_input_and_unsafe_source_file(self) -> None:
        with self.assertRaisesRegex(RequirementsError, "maximum size"):
            parse_requirements_text("a==1", max_bytes=1)
        with self.assertRaisesRegex(ValueError, "project-relative"):
            parse_requirements_text("a==1", source_file="C:\\private\\requirements.txt")

    def test_reads_utf8_file_and_rejects_invalid_encoding(self) -> None:
        temporary_root = PROJECT_ROOT / ".tmp"
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            valid_path = Path(directory) / "requirements.txt"
            valid_path.write_text("demo==1.2.3\n", encoding="utf-8")
            invalid_path = Path(directory) / "invalid-requirements.txt"
            invalid_path.write_bytes(b"\xff\xfe\x00")

            result = parse_requirements(valid_path)

            self.assertEqual(result.graph.components[0].id, "pkg:pypi/demo@1.2.3")
            with self.assertRaisesRegex(RequirementsError, "UTF-8"):
                parse_requirements(invalid_path)


if __name__ == "__main__":
    unittest.main()
