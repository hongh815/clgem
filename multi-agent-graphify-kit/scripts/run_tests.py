#!/usr/bin/env python3
"""Run Cogem tests from a source checkout without installing the package."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Cogem's unittest suite.")
    parser.add_argument("--pattern", default="test*.py", help="unittest discovery pattern")
    parser.add_argument("--quiet", action="store_true", help="Use concise test output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    for path in (root / "src", root):
        value = str(path)
        if value in sys.path:
            sys.path.remove(value)
        sys.path.insert(0, value)

    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern=args.pattern)
    result = unittest.TextTestRunner(verbosity=1 if args.quiet else 2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
