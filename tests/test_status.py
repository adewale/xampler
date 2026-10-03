from __future__ import annotations

from xampler.status import Progress


def test_progress_percent_is_bounded() -> None:
    assert Progress(5, 10).percent == 50.0
    assert Progress(5, 0).percent == 0.0
    assert Progress(12, 10).percent == 100.0
