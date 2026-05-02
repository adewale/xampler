# General API Shape for Pythonic Cloudflare Workers Examples

Last reviewed: 2026-05-01. Python anchor: **Python 3.13**.

## Goal

Each Cloudflare primitive should feel like a small Python service object over a binding, with Python-native handles for individual resources and explicit escape hatches for platform-specific behavior.

The pattern should generalize from R2 to KV, D1, Queues, Durable Objects, Workers AI, Vectorize, Workflows, and Cache.

## Recommended shape

```py
service = PrimitiveService(self.env.BINDING)
resource = service.resource("id-or-key")

await resource.write_text("hello")
value = await resource.read_text()
info = await resource.stat()

async for item in service.iter_items(prefix="..."):
    ...
```

For R2 specifically:

```py
r2 = R2Bucket(self.env.BUCKET)
obj = r2.object("notes/hello.txt")

await obj.write_text("hello")
text = await obj.read_text()
info = await obj.stat()
```

## Layers

### 1. Service wrapper

A service wrapper owns one Cloudflare binding and exposes operations that belong to the collection.

Examples:

| Primitive | Service wrapper | Collection-level operations |
|---|---|---|
| R2 | `R2Bucket` | `list`, `iter_objects`, `delete_many`, `create_multipart_upload` |
| KV | `KVNamespace` | `list`, `iter_keys`, bulk-like helpers if useful |
| D1 | `D1Database` | `execute`, `query`, `transaction-like helpers where possible` |
| Queues | `Queue` | `send`, `send_batch` |
| Durable Objects | `DurableObjectNamespace` | `id_from_name`, `get`, `stub` |
| Vectorize | `VectorIndex` | `query`, `insert`, `upsert`, `delete` |
| Workers AI | `AIService` | `run`, typed task helpers |
| Workflows | `WorkflowService` | `create`, `instance`, `status` |
| Cache | `CacheStore` | `match`, `put`, `delete` |

### 2. Resource handle

A resource handle represents a specific item inside the service. It should be lightweight and cheap to construct.

Examples:

| Primitive | Handle | Handle operations |
|---|---|---|
| R2 | `R2ObjectRef` | `read_text`, `write_text`, `read_bytes`, `write_bytes`, `stream`, `stat`, `delete`, `exists` |
| KV | `KVKey` | `get_text`, `put_text`, `get_json`, `put_json`, `delete`, `exists` |
| D1 | `D1Statement` / row models | `bind`, `first`, `all`, typed row conversion |
| Durable Objects | `DurableObjectRef` | `fetch`, typed RPC helpers |
| Workflow | `WorkflowInstance` | `status`, `terminate`, `restart` |

### 3. Option dataclasses

Use dataclasses for structured options instead of loose dictionaries when the options are part of the public teaching API.

Examples:

```py
R2HttpMetadata(cache_control="public, max-age=3600")
R2Range(offset=0, length=100)
R2Conditional(etag_matches=etag)
QueueMessage(body={"id": 1}, delay_seconds=30)
VectorQuery(top_k=10, namespace="docs")
```

### 4. Native Python return values

Prefer:

- `None` for absence.
- `str` for text.
- `bytes` for small binary data.
- `dict` / dataclass for JSON-like metadata.
- `AsyncIterator[T]` for streamed or paginated sequences.
- small result dataclasses for structured platform responses.

Avoid leaking `JsProxy` into app code unless the property is named `raw` and documented as an escape hatch.

### 5. Lifecycle support

If a platform operation has a lifecycle, support `async with`.

Examples:

```py
async with await r2.create_multipart_upload("video.mp4") as upload:
    part = await upload.upload_part(1, request.body)
    await upload.complete([part])
```

Future examples:

```py
async with d1.batch() as batch:
    batch.add(...)

async with queue.producer() as producer:
    await producer.send(...)
```

Only add context managers when there is real cleanup, batching, commit/rollback, or resource lifetime behavior.

## Naming conventions

Use Python verbs for Python concepts and Cloudflare nouns for platform concepts.

Good:

```py
await obj.read_text()
await obj.write_bytes(data)
await bucket.iter_objects(prefix="logs/")
await queue.send_json({"id": 1})
```

Also acceptable when teaching platform vocabulary:

```py
await bucket.put_text("key", "value")
await bucket.get_text("key")
```

Avoid exposing JavaScript naming as the primary API:

```py
# Avoid as primary API
await bucket.resumeMultipartUpload(...)
```

Expose raw platform APIs under `.raw` for advanced users.

## Generalization principle

Each example should provide three levels:

1. **Friendly path** — Pythonic methods: `read_text`, `write_json`, `iter_*`, `exists`.
2. **Platform path** — Cloudflare concepts: bindings, metadata, queues, workflows, vector indexes.
3. **Escape hatch** — `.raw` for JavaScript-native streams, exact Workers APIs, or unsupported features.

This keeps examples friendly without becoming misleading.
