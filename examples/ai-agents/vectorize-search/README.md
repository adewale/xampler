# Vectorize 17 — Search

Demonstrates typed vectors, upsert, query, get, delete, and describe. Create the index with matching dimensions before deploy.

## Cloudflare docs

- [Vectorize](https://developers.cloudflare.com/vectorize/)

## Copy this API

```python
from xampler.vectorize import VectorIndex, VectorQuery

index = VectorIndex(env.INDEX, dimensions=32)
result = await index.query(VectorQuery(values=[1.0] + [0.0] * 31))
```
