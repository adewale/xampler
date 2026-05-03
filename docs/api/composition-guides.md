# Copyable composition guides

Xampler should make Cloudflare primitives feel like a small set of Python concepts that compose:

```text
Service → Ref → Request → Result → Progress/Checkpoint → Verifier
```

## Pattern 1: R2 bytes to D1 searchable records

Use when a dataset lands in object storage and should become queryable.

```python
from xampler.d1 import D1Database
from xampler.r2 import R2Bucket
from xampler.status import BatchResult
from xampler.streaming import JsonlReader, StreamCheckpoint, aiter_batches

bucket = R2Bucket(env.ARTIFACTS)
db = D1Database(env.DB)
stream = await bucket.object("datasets/items.jsonl").byte_stream()

checkpoint = StreamCheckpoint("items", offset=0, records=0)
batches = 0
records = 0

async for batch in aiter_batches(JsonlReader(stream).records(), size=500):
    statements = [
        db.statement("INSERT INTO items(id, body) VALUES (?, ?)").bind(row["id"], row)
        for row in batch
    ]
    await db.batch_run(statements)
    batches += 1
    records += len(batch)
    checkpoint = StreamCheckpoint("items", offset=records, records=records)

result = BatchResult(batches=batches, records=records, checkpoint=checkpoint)
```

Route pattern:

```python
if path == "/pipeline/status":
    return json_response(await pipeline.status())
```

## Pattern 2: Queue-backed retryable work

Use when request handling should enqueue work instead of doing it inline.

```python
from xampler.queues import QueueConsumer, QueueJob, QueueService

queue = QueueService(env.JOBS)
await queue.send(QueueJob("index-object", {"key": "datasets/items.jsonl"}))
```

Consumer:

```python
async def queue(batch, env, ctx):
    result = await QueueConsumer().process_batch(batch)
    print(result)
```

Operational assertion:

```text
processed + retried + dead_lettered >= attempted messages
```

## Pattern 3: Workflow timeline plus D1 status

Use when a task has durable phases and users need visibility.

```python
from xampler.workflows import WorkflowService

workflow = WorkflowService(env.PIPELINE)
started = await workflow.start()
status = await workflow.status(started.instance_id)
```

Recommended app routes:

```text
POST /workflows/start
GET  /workflows/<id>/status
GET  /workflows/<id>/timeline
```

`/timeline` should return ordered events such as:

```json
[
  {"step": "fetch input", "state": "complete", "records": 100},
  {"step": "transform", "state": "running", "records": 50}
]
```

## Pattern 4: Retrieval-augmented answer from R2/D1/Vectorize/AI

Use when documents are stored in R2, indexed in D1/Vectorize, and summarized by AI.

```python
from xampler.ai import AIService, TextGenerationRequest
from xampler.d1 import D1Database
from xampler.vectorize import VectorIndex, VectorQuery

index = VectorIndex(env.INDEX, dimensions=32)
db = D1Database(env.DB)
ai = AIService(env.AI)

matches = await index.query(VectorQuery(values=query_vector, top_k=5))
rows = await db.query(
    "SELECT title, body FROM documents WHERE id IN ({})".format(
        ",".join("?" for _ in matches.matches)
    ),
    *[match.id for match in matches.matches],
)
answer = await ai.generate_text(TextGenerationRequest(f"Answer from context: {rows}"))
```

## Pattern 5: Durable Object/WebSocket room with transcript export

Use when many clients share state and the room should be observable.

Recommended routes:

```text
GET /rooms/<name>/status
GET /rooms/<name>/timeline
GET /rooms/<name>/transcript
```

Recommended result shape:

```python
@dataclass(frozen=True)
class RoomStatus:
    room: str
    connections: int
    messages: int
    state: OperationState = "running"
```

## API surface ideas

These ideas reuse existing Xampler vocabulary instead of adding a giant client:

1. `xampler.ops.OperationTimeline` — ordered events for workflows, queues, and Durable Objects.
2. `xampler.ops.TimelineEvent` — `{name, state, details}`.
3. `xampler.ops.PipelineStatus` — combines `Progress`, `Checkpoint`, and recent timeline events.
4. `xampler.ops.StatusReporter` — future tiny protocol for services that expose `status()`.
5. `xampler.testing.FakeBinding` helpers — future test fakes for docs, not runtime dependencies.

Only promote the future ideas after at least two examples need the same shape.
