"""Tests for the initial command-line contract."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

from supplyguard import __version__

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the real module entry point using the active project interpreter."""
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "supplyguard", *arguments],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


class CommandLineContractTest(unittest.TestCase):
    def test_version_option_reports_package_version(self) -> None:
        result = run_cli("--version")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"SupplyGuard {__version__}")

    def test_help_describes_the_product(self) -> None:
        result = run_cli("--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("software supply-chain security analysis", result.stdout)

    def test_unknown_option_fails_with_an_explanation(self) -> None:
        result = run_cli("--not-a-real-option")

        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)


if __name__ == "__main__":
    unittest.main()
