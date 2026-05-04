from __future__ import annotations

from xampler.status import BatchResult, Checkpoint, Progress


def test_progress_percent_is_bounded() -> None:
    assert Progress(5, 10).percent == 50.0
    assert Progress(5, 0).percent == 0.0
    assert Progress(12, 10).percent == 100.0


def test_checkpoint_and_batch_result_share_status_vocabulary() -> None:
    checkpoint = Checkpoint("import", offset=10, records=5, state="complete")
    result = BatchResult(batches=2, records=5, checkpoint=checkpoint)

    assert result.checkpoint.state == "complete"
    assert result.records == 5
