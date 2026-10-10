from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import settings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Property tests run a small fixed budget, and the same examples on every run, so a CI
# failure reproduces locally. The budget is a count of examples, not wall-clock time.
settings.register_profile("xampler", max_examples=100, derandomize=True, deadline=None)
# Deeper, randomized runs are on demand only:
#   uv run pytest tests/test_cli_fuzz.py --hypothesis-profile=deep
settings.register_profile("deep", max_examples=2000, deadline=None)
settings.load_profile("xampler")
