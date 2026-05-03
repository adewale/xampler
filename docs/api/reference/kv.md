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

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
