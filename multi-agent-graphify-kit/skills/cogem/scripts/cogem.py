#!/usr/bin/env python3
"""Portable launcher for the Cogem skill package."""

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
package_root = None
for parent in Path(__file__).resolve().parents:
    candidate = parent / "src" / "cogem" / "cli.py"
    if candidate.is_file():
        package_root = parent
        break

if package_root is not None:
    src = package_root / "src"
    filtered = []
    for entry in sys.path:
        try:
            resolved = Path(entry or ".").resolve()
        except OSError:
            filtered.append(entry)
            continue
        if resolved in {src.resolve(), SCRIPT_DIR.resolve()}:
            continue
        filtered.append(entry)
    sys.path[:] = [str(src), *filtered]

try:
    from cogem.cli import main
except ModuleNotFoundError as exc:
    raise SystemExit("Cogem runtime not found. Install the package or preserve the repository src/cogem directory.") from exc

raise SystemExit(main())
