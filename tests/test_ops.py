from __future__ import annotations

from xampler.ops import OperationTimeline, PipelineStatus, TimelineEvent
from xampler.status import Checkpoint, Progress


def test_operation_timeline_state() -> None:
    assert OperationTimeline("empty").state == "not_started"
    assert OperationTimeline("ok", [TimelineEvent("load", "complete")]).state == "complete"
    assert OperationTimeline(
        "running", [TimelineEvent("load", "complete"), TimelineEvent("index")]
    ).state == "running"
    assert OperationTimeline("failed", [TimelineEvent("load", "failed")]).state == "failed"


def test_pipeline_status_shape() -> None:
    status = PipelineStatus(
        name="import",
        progress=Progress(5, 10),
        checkpoint=Checkpoint("import", offset=5, records=5),
        timeline=OperationTimeline("import", [TimelineEvent("batch", "complete")]),
    )
    assert status.progress.percent == 50.0
    assert status.timeline is not None
    assert status.timeline.state == "complete"
