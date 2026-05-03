# KV 02 — Binding

Pythonic KV helpers for text, JSON, existence checks, deletes, and key listing.

Routes: `PUT /text/<key>`, `GET /text/<key>`, `PUT /json/<key>`, `GET /json/<key>`, `DELETE /keys/<key>`, `GET /keys?prefix=...`.

## Cloudflare docs

- [Workers KV](https://developers.cloudflare.com/kv/)

## Copy this API

```python
from xampler.kv import KVNamespace

kv = KVNamespace(env.KV)
await kv.key("profile:ada").write_json({"name": "Ada"})
profile = await kv.key("profile:ada").read_json()
```
