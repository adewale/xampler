# KV

## Import

```python
from xampler.kv import KVNamespace
```

## Copy this API

```python
kv = KVNamespace(env.KV)
await kv.key("profile:ada").write_json({"name": "Ada"})
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Text/JSON read/write | Supported | Local verifier covers common key-value paths. |
| `exists`, `delete`, `list`, `iter_keys` | Supported | Local verifier covers list/delete/missing behavior. |
| TTL/expiration | Caveated | Simple write option exists; richer behavior is not deeply verified. |
| Metadata/deployed namespace semantics | Not covered | Future wrapper/remote work. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
