#!/usr/bin/env python3
"""Repository-local Cogem launcher; requires no installation."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPT_DIR = Path(__file__).resolve().parent
filtered = []
for entry in sys.path:
    try:
        resolved = Path(entry or ".").resolve()
    except OSError:
        filtered.append(entry)
        continue
    if resolved in {SRC.resolve(), SCRIPT_DIR.resolve()}:
        continue
    filtered.append(entry)
sys.path[:] = [str(SRC), *filtered]

from cogem.cli import main  # noqa: E402

raise SystemExit(main())
