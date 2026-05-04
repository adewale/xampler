# `xampler.status`

Canonical status vocabulary for long-running, resumable, and batched work.

```python
from xampler.status import BatchResult, Checkpoint, Progress

progress = Progress(current=50, total=100)
checkpoint = Checkpoint("gutenberg", offset=50, records=50)
result = BatchResult(batches=5, records=500, checkpoint=checkpoint)
```

Use product-specific statuses when Cloudflare has product-specific state, such as `WorkflowStatus`, `WebSocketStatus`, or `QueueBatchResult`. Use `Progress`, `Checkpoint`, and `BatchResult` as the shared building blocks for imports, pipelines, and route-level status responses.
