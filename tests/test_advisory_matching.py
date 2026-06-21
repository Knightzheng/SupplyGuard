"""Tests for explainable component-to-advisory matching."""

import json
import unittest
from pathlib import Path

from supplyguard.advisories import parse_osv, parse_osv_text
from supplyguard.domain import Component, Ecosystem
from supplyguard.matching import MatchMethod, match_advisory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "osv" / "OSV-SYNTHETIC-0001.json"


class AdvisoryMatchingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.advisory = parse_osv(FIXTURE)

    def test_matches_npm_semver_range_and_reports_fixed_version(self) -> None:
        component = Component(Ecosystem.NPM, "@example/vulnerable", "1.1.0")

        result = match_advisory(self.advisory, component)

        self.assertTrue(result.affected)
        self.assertEqual(result.matches[0].method, MatchMethod.SEMVER_RANGE)
        self.assertEqual(result.matches[0].fixed_versions, ("1.2.0",))
        self.assertEqual(result.warnings, ())

    def test_fixed_boundary_is_not_affected(self) -> None:
        component = Component(Ecosystem.NPM, "@example/vulnerable", "1.2.0")

        result = match_advisory(self.advisory, component)

        self.assertFalse(result.affected)
        self.assertEqual(result.matches, ())

    def test_matches_explicit_npm_and_pypi_versions(self) -> None:
        npm_result = match_advisory(
            self.advisory,
            Component(Ecosystem.NPM, "@EXAMPLE/VULNERABLE", "0.9.9"),
        )
        pypi_result = match_advisory(
            self.advisory,
            Component(Ecosystem.PYPI, "friendly-bard_tools", "3.1.4"),
        )

        self.assertEqual(npm_result.matches[0].method, MatchMethod.EXPLICIT_VERSION)
        self.assertEqual(pypi_result.matches[0].method, MatchMethod.EXPLICIT_VERSION)

    def test_different_package_is_not_matched(self) -> None:
        result = match_advisory(
            self.advisory,
            Component(Ecosystem.NPM, "unrelated", "1.1.0"),
        )

        self.assertFalse(result.affected)
        self.assertEqual(result.warnings, ())

    def test_unsupported_ecosystem_range_returns_structured_warning(self) -> None:
        advisory = parse_osv_text(
            json.dumps(
                {
                    "id": "OSV-PYPI-RANGE",
                    "modified": "2026-06-21T00:00:00Z",
                    "affected": [
                        {
                            "package": {"ecosystem": "PyPI", "name": "demo"},
                            "ranges": [
                                {
                                    "type": "ECOSYSTEM",
                                    "events": [
                                        {"introduced": "1.0"},
                                        {"fixed": "2.0"},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            )
        )

        result = match_advisory(advisory, Component(Ecosystem.PYPI, "demo", "1.5"))

        self.assertFalse(result.affected)
        self.assertEqual(result.warnings[0].code, "unsupported-version-range")
        self.assertIn("ECOSYSTEM", result.warnings[0].message)


if __name__ == "__main__":
    unittest.main()
