# Vectorize

## Import

```python
from xampler.vectorize import VectorIndex, Vector, VectorQuery
```

## Copy this API

```python
index = VectorIndex(env.INDEX, dimensions=32)
await index.upsert([Vector("doc-1", [1.0] + [0.0] * 31)])
```

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
