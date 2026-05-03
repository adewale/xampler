# Pipeline vocabulary

Xampler's compositional story is:

```text
Cloudflare binding/client → typed service → refs/requests/results → progress/checkpoint → verifier
```

For data pipelines, the memorable path is:

```text
R2 bytes → ByteStream → records → batches → D1/FTS → Queue → Vectorize/AI → status endpoint
```

## Operational vocabulary

| Concept | Xampler API |
|---|---|
| Active product binding | `R2Bucket`, `D1Database`, `KVNamespace`, `QueueService`, `VectorIndex` |
| Passive resource handle | `R2ObjectRef`, `KVKey`, `DurableObjectRef`, `WorkflowInstance` |
| Request shape | dataclasses such as `TextGenerationRequest`, `VectorQuery`, `ChatRequest` |
| Result shape | dataclasses such as `WorkflowStatus`, `BatchResult`, `ChatResponse` |
| Progress | `Progress(current, total, state)` |
| Checkpoint | `Checkpoint` / `StreamCheckpoint` |
| Retry/DLQ | `QueueConsumer`, `QueueBatchResult`, tracker refs |
| Local realism | explicit `Demo*` clients |
| Escape hatch | `.raw` |

## API narrative

Xampler should read like normal Python while keeping Cloudflare names visible:

```python
bucket = R2Bucket(env.BUCKET)
stream = bucket.object("dataset/items.jsonl").byte_stream()

async for batch in aiter_batches(JsonlReader(stream).records(), size=100):
    await db.batch_run([...])
```

The examples are not the API. Examples prove the API works in local and deployed Workers.
