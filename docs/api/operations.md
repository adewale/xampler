# Operations API: progress, checkpoints, retries, and observability

Xampler examples should expose operational state as typed Python values first, then serialize those values at the Worker route boundary.

## Core vocabulary

```python
from xampler.ops import OperationTimeline, PipelineStatus, TimelineEvent
from xampler.status import BatchResult, Checkpoint, Progress
from xampler.queues import QueueBatchResult, QueueConsumer, QueueJob, QueueService
from xampler.workflows import WorkflowService, WorkflowStatus
```

| Concept | Use when | API |
|---|---|---|
| Progress | A known-size task is underway. | `Progress(current, total, state)` |
| Checkpoint | A stream/import can resume from an offset. | `Checkpoint` or `StreamCheckpoint` |
| Batch result | Work is processed in bounded groups. | `BatchResult[T]` |
| Retry | One event/message failed but the batch should continue. | `QueueConsumer.process_batch()` |
| DLQ | A message exceeded normal handling and needs inspection. | `QueueBatchResult.dead_lettered` |
| Workflow status | A durable workflow instance has lifecycle state. | `WorkflowStatus` |
| Timeline | A process has ordered operational events. | `TimelineEvent`, `OperationTimeline` |
| Pipeline status | A route should expose progress, checkpoint, and events together. | `PipelineStatus` |

## Recommended route shape

Keep the operational logic in a service and make the route only serialize the result:

```python
from xampler.response import json_response
from xampler.status import Progress

async def fetch(request):
    progress = Progress(current=42, total=100)
    return json_response(progress)
```

## Checkpointed ingestion pattern

```python
from xampler.status import BatchResult
from xampler.streaming import StreamCheckpoint, aiter_batches

checkpoint = StreamCheckpoint("import", offset=0, records=0)
batches = 0
records = 0

async for batch in aiter_batches(records_from_stream(), size=500):
    await sink.insert_batch(batch)
    batches += 1
    records += len(batch)
    checkpoint = StreamCheckpoint("import", offset=records, records=records)

result = BatchResult(batches=batches, records=records, checkpoint=checkpoint)
```

## Queue retry pattern

```python
from xampler.queues import QueueConsumer

async def queue(batch, env, ctx):
    result = await QueueConsumer().process_batch(batch)
    print(result)
```

The default consumer isolates per-message failures, acknowledges successes, and retries failures with bounded backoff. Examples that need product-specific behavior should subclass or wrap the consumer instead of hiding Cloudflare Queue vocabulary.

## Workflow status pattern

```python
from xampler.workflows import WorkflowService

workflow = WorkflowService(env.PIPELINE)
started = await workflow.start()
status = await workflow.status(started.instance_id)
```

## Observability rules

1. Every long-running example should have a `/status` or `/progress` route.
2. Every resumable import should persist a checkpoint outside process memory.
3. Every queue example should report processed/retried/dead-lettered counts.
4. Every remote verifier should assert a real observable effect, not only HTTP 200.
5. Keep local `Demo*` status deterministic and label it as demo output.

## Current gaps

- Add a Workflows timeline example backed by D1.
- Add richer Queue tracker tests around deployed DLQ cleanup.
- Add route-level tests for Gutenberg and HVSC pipeline status endpoints.
