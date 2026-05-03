# Vectorize

## Import

```python
from xampler.vectorize import Vector, VectorIndex, VectorQuery, unit_vector
```

## Copy this API

```python
index = VectorIndex(env.INDEX, dimensions=32)
await index.upsert([Vector("doc-1", [1.0] + [0.0] * 31)])
result = await index.query(VectorQuery(values=[1.0] + [0.0] * 31, top_k=1))
```

## Main classes

- `VectorIndex(raw, dimensions=None)` wraps a Vectorize binding.
- `Vector` models an inserted vector.
- `VectorQuery` models query options.
- `VectorQueryResult` and `VectorMatch` model search results.
- `DemoVectorIndex` gives deterministic local search and keyword scoring.

## Common methods

```python
await index.upsert([vector])
await index.query(VectorQuery(values=values, top_k=5))
await index.query_by_id("doc-1")
await index.get(["doc-1"])
await index.delete(["doc-1"])
await index.describe()
```

## Testability

Set `dimensions` in tests to catch vector length mistakes. Use `DemoVectorIndex` for account-free local checks and fake bindings for raw response parsing.

## Runtime notes

Vectorize is account-backed. Local examples use demo vectors; deployed verification creates/uses a real index through the explicit remote lifecycle.
