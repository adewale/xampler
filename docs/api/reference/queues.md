# Queues

## Import

```python
from xampler.queues import QueueJob, QueueService, QueueConsumer
```

## Copy this API

```python
queue = QueueService(env.JOBS)
await queue.send(QueueJob("resize", {"image": "r2://bucket/key.jpg"}))
```

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
