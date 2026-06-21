"""Tests for OSV advisory models and event range semantics."""

import json
import tempfile
import unittest
from pathlib import Path

from supplyguard.advisories import (
    AdvisoryParseError,
    EventKind,
    InvalidSemanticVersionError,
    RangeType,
    SemanticVersion,
    UnsupportedVersionRangeError,
    parse_osv,
    parse_osv_text,
)
from supplyguard.domain import Ecosystem

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "osv" / "OSV-SYNTHETIC-0001.json"


class OsvAdvisoryTest(unittest.TestCase):
    def test_parses_package_identity_aliases_and_timestamps(self) -> None:
        advisory = parse_osv(FIXTURE)

        self.assertEqual(advisory.id, "OSV-SYNTHETIC-0001")
        self.assertEqual(advisory.aliases, ("CVE-2099-0001",))
        self.assertIsNotNone(advisory.published)
        self.assertIsNotNone(advisory.modified.tzinfo)
        self.assertEqual(len(advisory.affected), 2)
        self.assertEqual(advisory.affected[0].ecosystem, Ecosystem.NPM)
        self.assertEqual(advisory.affected[0].name, "@example/vulnerable")
        self.assertEqual(advisory.affected[1].name, "friendly-bard-tools")

    def test_semver_events_respect_inclusive_and_exclusive_boundaries(self) -> None:
        advisory = parse_osv(FIXTURE)
        affected = advisory.affected[0]
        version_range = affected.ranges[0]
        last_affected_range = affected.ranges[1]

        self.assertEqual(version_range.type, RangeType.SEMVER)
        self.assertEqual(version_range.events[0].kind, EventKind.INTRODUCED)
        self.assertTrue(affected.explicitly_affects("0.9.9"))
        self.assertTrue(version_range.contains("1.0.0"))
        self.assertTrue(version_range.contains("1.1.9"))
        self.assertFalse(version_range.contains("1.2.0"))
        self.assertTrue(last_affected_range.contains("2.0.5"))
        self.assertFalse(last_affected_range.contains("2.0.6"))
        self.assertEqual(version_range.fixed_versions, ("1.2.0",))

    def test_semver_comparison_handles_prerelease_and_open_start(self) -> None:
        advisory = parse_osv_text(
            json.dumps(
                {
                    "id": "OSV-SYNTHETIC-PRERELEASE",
                    "modified": "2026-06-21T00:00:00Z",
                    "affected": [
                        {
                            "package": {"ecosystem": "npm", "name": "demo"},
                            "ranges": [
                                {
                                    "type": "SEMVER",
                                    "events": [
                                        {"introduced": "0"},
                                        {"fixed": "1.0.0"},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            )
        )
        version_range = advisory.affected[0].ranges[0]

        self.assertTrue(version_range.contains("0.1.0"))
        self.assertTrue(version_range.contains("1.0.0-rc.1"))
        self.assertFalse(version_range.contains("1.0.0"))

    def test_rejects_invalid_event_sequences_and_timestamps(self) -> None:
        invalid_payloads = (
            {
                "id": "OSV-NO-INTRODUCED",
                "modified": "2026-06-21T00:00:00Z",
                "affected": [
                    {
                        "package": {"ecosystem": "npm", "name": "demo"},
                        "ranges": [{"type": "SEMVER", "events": [{"fixed": "1.0.0"}]}],
                    }
                ],
            },
            {
                "id": "OSV-MIXED-END",
                "modified": "2026-06-21T00:00:00Z",
                "affected": [
                    {
                        "package": {"ecosystem": "npm", "name": "demo"},
                        "ranges": [
                            {
                                "type": "SEMVER",
                                "events": [
                                    {"introduced": "1.0.0"},
                                    {"fixed": "1.1.0"},
                                    {"introduced": "2.0.0"},
                                    {"last_affected": "2.1.0"},
                                ],
                            }
                        ],
                    }
                ],
            },
            {"id": "OSV-BAD-TIME", "modified": "not-a-time", "affected": []},
        )

        for payload in invalid_payloads:
            with self.subTest(advisory_id=payload["id"]), self.assertRaises(AdvisoryParseError):
                parse_osv_text(json.dumps(payload))

    def test_preserves_but_does_not_compare_unsupported_range_type(self) -> None:
        advisory = parse_osv_text(
            json.dumps(
                {
                    "id": "OSV-ECOSYSTEM-RANGE",
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

        with self.assertRaises(UnsupportedVersionRangeError):
            advisory.affected[0].ranges[0].contains("1.5")

    def test_semver_precedence_matches_the_standard_sequence(self) -> None:
        ordered = (
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-alpha.beta",
            "1.0.0-beta",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0-rc.1",
            "1.0.0",
        )

        parsed = tuple(SemanticVersion.parse(version) for version in ordered)

        self.assertEqual(tuple(sorted(reversed(parsed))), parsed)
        self.assertEqual(SemanticVersion.parse("1.0.0+build.7"), SemanticVersion.parse("1.0.0"))
        with self.assertRaises(InvalidSemanticVersionError):
            SemanticVersion.parse("1.0.0-01")

    def test_rejects_large_and_non_utf8_osv_files(self) -> None:
        with self.assertRaisesRegex(AdvisoryParseError, "maximum size"):
            parse_osv_text("{}", max_bytes=1)

        temporary_root = PROJECT_ROOT / ".tmp"
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            invalid_path = Path(directory) / "invalid-osv.json"
            invalid_path.write_bytes(b"\xff\xfe\x00")

            with self.assertRaisesRegex(AdvisoryParseError, "UTF-8"):
                parse_osv(invalid_path)


if __name__ == "__main__":
    unittest.main()
