# API reference

This is a concise hand-written reference for the importable Xampler library surface.

## Storage and data

```python
from xampler.r2 import R2Bucket, R2HttpMetadata, R2Range
from xampler.d1 import D1Database
from xampler.kv import KVNamespace
```

```python
bucket = R2Bucket(env.BUCKET)
await bucket.object("notes/a.txt").write_text("hello")
text = await bucket.object("notes/a.txt").read_text()
```

```python
db = D1Database(env.DB)
row = await db.statement("SELECT * FROM quotes WHERE author = ?").one("PEP 20")
```

```python
kv = KVNamespace(env.KV)
await kv.key("profile:ada").write_json({"name": "Ada"})
profile = await kv.key("profile:ada").read_json()
```

## Events and state

```python
from xampler.queues import QueueJob, QueueService, QueueConsumer
```

```python
queue = QueueService(env.JOBS)
await queue.send(QueueJob("resize", {"image": "r2://bucket/key.jpg"}))
```

## AI and search

```python
from xampler.ai import AIService, TextGenerationRequest
from xampler.vectorize import VectorIndex, Vector, VectorQuery
```

```python
ai = AIService(env.AI)
result = await ai.generate_text(TextGenerationRequest("Summarize this dataset"))
```

```python
index = VectorIndex(env.INDEX, dimensions=32)
await index.upsert([Vector("doc-1", [1.0] + [0.0] * 31)])
matches = await index.query(VectorQuery(values=[1.0] + [0.0] * 31, top_k=1))
```

## REST-backed Cloudflare products

```python
from xampler.browser_rendering import BrowserRendering, ScreenshotRequest
from xampler.r2_sql import R2SqlClient, R2SqlQuery
from xampler.r2_data_catalog import R2DataCatalog
```

These clients require Worker runtime secrets/tokens and are currently experimental.

## Runtime helpers

```python
from xampler.streaming import ByteStream, JsonlReader, aiter_batches
from xampler.response import jsonable
from xampler.status import Progress, Checkpoint
from xampler.cloudflare import CloudflareService, ResourceRef, RestClient
```
