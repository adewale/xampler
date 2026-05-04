# Composition and operations

Xampler's small compositional vocabulary is:

```text
Service → Ref → Request → Result → Progress/Checkpoint → Timeline → Verifier
```

For data pipelines, the memorable path is:

```text
R2 bytes → ByteStream → records → batches → D1/FTS → Queue → Vectorize/AI → status endpoint
```

## Vocabulary

| Concept | Use when | API |
|---|---|---|
| Service | Active wrapper around a Worker binding/runtime facade. | `R2Bucket`, `D1Database`, `QueueService`, `VectorIndex` |
| Ref | Cheap handle to a named resource reached through a service/namespace. | `R2ObjectRef`, `KVKey`, `DurableObjectRef`, `WorkflowInstance` |
| REST client | Token/HTTP-backed product client when no Python-usable binding path exists. | `BrowserRendering`, `R2SqlClient`, `R2DataCatalog`, `AIGateway` |
| Request | Input shape. | `TextGenerationRequest`, `VectorQuery`, `ChatRequest` |
| Result | Output shape. | `WorkflowStatus`, `BatchResult`, `ChatResponse` |
| Progress | A known-size task is underway. | `Progress(current, total, state)` |
| Checkpoint | A stream/import can resume from an offset. | `Checkpoint`, `StreamCheckpoint` |
| Timeline | A process has ordered operational events. | `TimelineEvent`, `OperationTimeline` |
| Pipeline status | A route should expose progress, checkpoint, and events together. | `PipelineStatus` |
| Retry/DLQ | Queue work can fail independently. | `QueueConsumer`, `QueueBatchResult` |
| Local realism | Account-backed products need deterministic local behavior. | explicit `Demo*` clients |
| Escape hatch | Advanced platform behavior is still available. | `.raw` |

## Route-level rules

1. Keep route handlers thin.
2. Put reusable product behavior in `xampler/` services/refs.
3. Return dataclasses or native Python values from services.
4. Serialize once at the route boundary with `json_response()` or `Response.json()`.
5. Every long-running example should expose `/status` or `/progress`.
6. Every resumable import should persist a checkpoint outside process memory.
7. Every queue example should report processed/retried/dead-lettered counts.
8. Every remote verifier should assert an observable effect, not only HTTP 200.

```python
from xampler.response import json_response
from xampler.status import Progress

async def fetch(request):
    progress = Progress(current=42, total=100)
    return json_response(progress)
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

## Pattern 3: Workflow timeline plus status

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
  {"name": "fetch input", "state": "complete", "details": {"records": 100}},
  {"name": "transform", "state": "running", "details": {"records": 50}}
]
```

## Pattern 4: Retrieval answer from R2/D1/Vectorize/AI

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
from dataclasses import dataclass
from xampler.status import OperationState

@dataclass(frozen=True)
class RoomStatus:
    room: str
    connections: int
    messages: int
    state: OperationState = "running"
```

## Future API ideas to resist until proven

- `StatusReporter` protocol.
- `xampler.testing` fake bindings.
- Larger pipeline/orchestration framework.

Only promote more API after at least two examples need the same shape.
