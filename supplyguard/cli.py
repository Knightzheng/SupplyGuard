"""Command-line entry point for SupplyGuard."""

import argparse
from collections.abc import Sequence

from supplyguard import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the dependency-free bootstrap command parser."""
    parser = argparse.ArgumentParser(
        prog="supplyguard",
        description="Offline-first software supply-chain security analysis.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"SupplyGuard {__version__}",
        help="show the SupplyGuard version and exit",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and return a process exit code."""
    build_parser().parse_args(argv)
    return 0


def main() -> None:
    """Run the command-line application."""
    raise SystemExit(run())
