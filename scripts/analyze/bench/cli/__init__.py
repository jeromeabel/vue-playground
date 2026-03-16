"""CLI entry point for the bench command."""

from __future__ import annotations

import argparse
import sys

from .analyze import register as register_analyze
from .compare import register as register_compare


def main(argv: list[str] | None = None) -> None:
    """Run the bench CLI."""
    parser = argparse.ArgumentParser(
        prog="bench",
        description="Benchmark analysis tools for vue-playground",
    )
    subparsers = parser.add_subparsers(dest="command")

    register_analyze(subparsers)
    register_compare(subparsers)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        raise SystemExit(1)

    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
