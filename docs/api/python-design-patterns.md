# Reused Python Design Patterns

Last reviewed: 2026-05-01. Python anchor: Python 3.13.

These are the patterns we repeatedly use to make Cloudflare primitives feel natural to Python developers without hiding the Cloudflare platform.

## 1. Service object over binding

Wrap each Cloudflare binding in a small service class.

```py
bucket = R2Bucket(self.env.BUCKET)
kv = KVNamespace(self.env.KV)
queue = QueueService(self.env.JOBS)
index = VectorIndex(self.env.INDEX)
```

Why: the Worker entrypoint stays thin, and platform conversion logic has one home.

## 2. Resource handle for named things

When a primitive has named resources, expose a lightweight handle.

```py
obj = bucket.object("notes/hello.txt")
key = kv.key("session:123")
counter = counters.named("global")
```

Why: this borrows from `pathlib` and makes common operations discoverable.

## 3. Friendly verbs plus platform verbs

Expose Python-friendly verbs while keeping Cloudflare vocabulary available.

```py
await obj.write_text("hello")      # friendly Python layer
await bucket.put_text(key, text)    # platform/object-storage layer
```

Why: beginners get familiar APIs; advanced users can still map code to Cloudflare docs.

## 4. Dataclasses for options and results

Use dataclasses for structured options and response models.

```py
R2HttpMetadata(cache_control="public, max-age=3600")
R2Range(offset=0, length=1024)
VectorQuery(values=[...], top_k=5)
QueueJob(kind="resize", payload={"image": "a.jpg"})
```

Why: dataclasses are inspectable, typed, testable, and easier to document than raw JS-shaped dictionaries.

## 5. `None` for absence

Missing keys, objects, and rows should become `None`.

```py
text = await bucket.read_text("missing.txt")  # None
row = await db.query_one("SELECT ...")        # None
```

Why: this is the normal Python optional-value pattern and avoids leaking JavaScript `null`/`undefined`.

## 6. Async iteration for pagination and streams

Use `async for` when the platform returns pages, cursors, batches, or streams.

```py
async for obj in bucket.iter_objects(prefix="logs/"):
    ...

async for key in kv.iter_keys(prefix="session:"):
    ...
```

Why: Python developers expect iteration instead of manual cursor loops.

## 7. Async context managers for lifecycles

Use `async with` for APIs that need cleanup, commit, abort, or close semantics.

```py
async with await bucket.create_multipart_upload("large.bin") as upload:
    part = await upload.upload_part(1, request.body)
    await upload.complete([part])
```

Why: resource lifecycles become explicit and safer.

## 8. Boundary conversion at the edge

Keep `cfboundary` calls inside service wrappers, not business logic.

```py
await self.raw.send(to_js(body))
return to_py(await self.raw.describe())
```

Why: app code should see Python values; wrapper code handles Pyodide/JS semantics.

## 9. `.raw` escape hatch

Expose the underlying JavaScript binding/object when needed.

```py
return Response(obj.raw.body)  # direct JS stream for large R2 object
```

Why: Cloudflare APIs move quickly, and streaming/performance-sensitive paths sometimes need native Workers objects.

## 10. Literate comments for platform surprises

Comments should explain why the platform shape matters, not restate Python syntax.

Good comments explain:

- why static assets should bypass Python;
- why R2 large bodies should remain JS streams;
- why Durable Objects coordinate WebSockets;
- why `create_proxy()` is needed for JS event listeners;
- why queue messages must be explicitly acked or retried.

## 11. Verifier-first examples

Each example should grow a `scripts/verify_examples.py` path.

Why: examples should be runnable and falsifiable, not just plausible code snippets.

## 12. Three-layer API rule

Every primitive should converge on:

1. **Friendly Python layer** — handles, `read_*`, `write_*`, `iter_*`, `exists`.
2. **Cloudflare platform layer** — product vocabulary and advanced options.
3. **Escape hatch** — `.raw` or low-level client for unwrapped APIs.
