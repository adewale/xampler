# Top 10 Primitive Improvement Plan

Last reviewed: 2026-05-01.

This focuses on the primitives most important to an average Python developer:

1. Workers
2. R2
3. D1
4. Workers KV
5. Queues
6. Workers AI
7. Vectorize
8. Durable Objects
9. Assets / Pages
10. Cron Triggers

The goal is to improve three metrics together:

- **Coverage** — more of the useful Cloudflare API surface is demonstrated.
- **Pythonic API** — the example feels natural to Python developers.
- **Test realism** — the example is actually run and verified.

## Current state and target next step

| Rank | Primitive | Current coverage | Current Pythonic API | Current realism | Highest-impact next improvement |
|---:|---|---:|---:|---:|---|
| 1 | Workers | 6.0 | 8.0 | 3 | Add shared `response()`/`json_response()` helper and request parsing helper used by all examples. |
| 2 | R2 | 8.5 | 9.25 | 4 | Verify multipart upload locally and add object-handle docs for all advanced options. |
| 3 | D1 | 6.8 | 8.5 | 3 | Add write/query mutation route, index usage, retries, and remote/deployed D1 verification. |
| 4 | KV | 7.5 | 8.5 | 3 | Verify JSON, delete, list, and `iter_keys()`; add metadata/expiration docs. |
| 5 | Queues | 7.5 | 8.25 | 1 | Add local enqueue verification and consumer processing harness; document ack/retry patterns. |
| 6 | Workers AI | 5.5 | 8.25 | 1 | Add typed response model and a deterministic smoke path for a small inference. |
| 7 | Vectorize | 7.0 | 8.0 | 1 | Add `VectorMatch`/`VectorQueryResult`, batch helper, and upsert/query verification. |
| 8 | Durable Objects | 6.5 | 8.25 | 3 | Add typed `DurableObjectRef`, verify named-object isolation and concurrent increments. |
| 9 | Assets / Pages | 6.0 | 8.4 | 3/1 | Assets: verify dynamic route plus static route. Pages: add Pages dev verifier. |
| 10 | Cron Triggers | 6.0 | 8.0 | 2 | Verify local scheduled endpoint and record an observable side effect. |

## Pythonic API improvements by primitive

### Workers

Current: each example has small response helpers or direct `Response` usage.

Make more Pythonic:

```py
return json_response({"ok": True})
route = RequestInfo.from_request(request)
```

Add shared helper module once duplication becomes painful.

### R2

Current: strongest API surface.

Keep improving:

```py
obj = bucket.object("image.jpeg")
await obj.write_bytes(data, content_type="image/jpeg")
assert await obj.exists()

async with await bucket.create_multipart_upload("large.bin") as upload:
    ...
```

Next: multipart verifier and presigned/S3-compatible companion example.

### D1

Current: `D1Database.query()`, `query_one()`, and `D1Statement`.

Make more Pythonic with statement handles:

```py
stmt = db.statement("SELECT * FROM users WHERE id = ?")
row = await stmt.one(user_id)
rows = await stmt.all(active=True)
```

The example now verifies local D1 setup with `db_init.sql` before starting the Worker. Continue expanding row dataclass factories:

```py
quote = await stmt.one_as(Quote)
```

### KV

Current: `KVNamespace`, `KVKey`, `iter_keys()`.

Next:

```py
session = kv.key("session:123")
await session.write_json(data, expiration_ttl=3600)
async for key in kv.iter_keys(prefix="session:"):
    await key.delete()
```

Verify JSON/list/delete paths.

### Queues

Current: `QueueService`, `QueueJob`, `QueueConsumer`.

Make more Pythonic:

```py
await queue.send(QueueJob("resize", {"image": key}))
await queue.send_many(jobs)

async for message in QueueBatch(batch):
    async with message.processing():
        await handle(message.body)
```

Be careful: Queues require explicit ack/retry, so context managers must be very clear.

### Workers AI

Current: `AIService.generate_text(TextGenerationRequest(...))`.

Make more Pythonic:

```py
response = await ai.text.generate("Explain R2", model="...")
print(response.text)
```

Keep platform path:

```py
await ai.run(model, inputs)
```

### Vectorize

Current: `VectorIndex`, `Vector`, `VectorQuery`.

Make more Pythonic:

```py
await index.upsert([Vector("doc-1", embedding, metadata={"kind": "doc"})])
results = await index.search(embedding, top_k=5)
for match in results.matches:
    print(match.id, match.score)
```

Add result dataclasses.

### Durable Objects

Current: named counter wrapper.

Make more Pythonic:

```py
counter = counters.named("global")
value = await counter.increment()
await counter.reset()
```

Keep raw stub escape hatch.

### Assets / Pages

Assets API should remain mostly configuration-first:

```py
# No Python API needed for static files.
# The Pythonic move is to avoid waking Python.
```

Pages is not Python-native today, so score should depend on clarity and tooling honesty rather than Python API wrappers.

### Cron Triggers

Current: `ScheduledJob.run()`.

Make more Pythonic:

```py
@dataclass(frozen=True)
class ScheduledEventInfo:
    cron: str
    scheduled_time: datetime

await job.run(ScheduledEventInfo.from_event(event))
```

Add testable job logic independent of Workers runtime.

## Metric strategy

Prioritize improvements in this order:

1. Raise **test realism** for top 10 to at least level 3.
2. Raise **coverage** by adding the next most common operation per primitive.
3. Raise **Pythonic API** only when it does not hide Cloudflare concepts.

R2 is the model: it has friendly handles, platform methods, advanced options, `.raw`, and a byte-for-byte verifier.
