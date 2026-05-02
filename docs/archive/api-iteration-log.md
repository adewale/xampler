# API Iteration Log

Last updated: 2026-05-01.

## Iteration 1: R2 object handles

Added a pathlib-inspired object handle:

```py
obj = bucket.object("notes/hello.txt")
await obj.write_text("hello")
text = await obj.read_text()
info = await obj.stat()
await obj.delete()
```

Why this is more Pythonic:

- It gives a specific object a small object of its own.
- It uses familiar file/path verbs: `read_text`, `write_text`, `read_bytes`, `write_bytes`, `exists`, `stat`.
- It keeps R2 platform vocabulary available through `put_*`, `get`, `head`, `list`, multipart APIs, and `.raw`.

## Iteration 2: KV key handles and iteration

Extended the KV example with:

```py
kv = KVNamespace(self.env.KV)
key = kv.key("session:123")

await key.write_json({"user_id": 123})
data = await key.read_json()

async for key in kv.iter_keys(prefix="session:"):
    print(key.name)
```

Also added aliases for platform vocabulary:

```py
await key.put_text("value")
value = await key.get_text()
```

Why this is more Pythonic:

- `KVKey` is a resource handle like `R2ObjectRef`.
- `iter_keys()` hides cursor pagination behind `async for` while keeping `list()` available.
- Friendly Python verbs and Cloudflare platform verbs both exist, so the API can teach without trapping advanced users.

## General rule going forward

Every primitive should expose three layers:

1. Friendly Python handle methods.
2. Cloudflare platform methods/options.
3. `.raw` or equivalent escape hatch for unwrapped runtime APIs.
