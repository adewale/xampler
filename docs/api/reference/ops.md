# Operations

## Import

```python
from xampler.ops import OperationTimeline, PipelineStatus, TimelineEvent
from xampler.status import Checkpoint, Progress
```

## Copy this API

```python
timeline = OperationTimeline(
    "import-1",
    [
        TimelineEvent("fetch", "complete", {"records": 100}),
        TimelineEvent("index", "running", {"records": 50}),
    ],
)
status = PipelineStatus(
    name="gutenberg-import",
    progress=Progress(current=50, total=100),
    checkpoint=Checkpoint("gutenberg", offset=50, records=50),
    timeline=timeline,
)
```

## Route pattern

```python
if path == "/pipeline/status":
    return json_response(status)
```

Use this shape when an example needs visible progress, checkpoints, and recent operational events.
