"""Allow running skillforge as `python -m skillforge`."""

from __future__ import annotations

import os
import sys

# Force UTF-8 output on Windows to avoid encoding errors with Rich/Unicode
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from skillforge.cli.main import main

main()
