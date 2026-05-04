# Queues

## Import

```python
from xampler.queues import QueueConsumer, QueueEventRecorder, QueueJob, QueueSendOptions, QueueService
```

## Copy this API

```python
queue = QueueService(env.JOBS)
await queue.send(QueueJob("resize", {"image": "r2://bucket/key.jpg"}))
await queue.send(QueueJob("delayed", {}), QueueSendOptions(delay_seconds=30))
```

## Main classes

- `QueueService(raw)` wraps a queue producer binding.
- `QueueJob(kind, payload)` is the default typed job envelope.
- `QueueConsumer` handles per-message ack/retry decisions.
- `QueueEventRecorder` is a Protocol for optional observability sinks; it is not tied to any Queue product API.
- `QueueBatchResult` reports processed/retried/dead-lettered counts.

## Consumer pattern

```python
async def queue(batch, env, ctx):
    result = await QueueConsumer().process_batch(batch)
    print(result)
```

## Testability

Use fake bindings with `send()` and `sendBatch()`. For consumers, fake messages with `body`, `attempts`, `ack()`, and `retry(options)`. Assert retry delay and ack behavior directly.

## Runtime notes

Local verification can exercise producer shape and deterministic consumer harnesses. Real delivery, retry timing, and DLQ observation require deployed Queue resources and are intentionally covered by opt-in remote verification.
