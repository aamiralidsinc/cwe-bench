"""Make the shared dashboard driver importable from the copied suite."""

from __future__ import annotations

import sys
from pathlib import Path

_SUPPORT = Path(__file__).resolve().parent.parent / "support"
if str(_SUPPORT) not in sys.path:
    sys.path.insert(0, str(_SUPPORT))
