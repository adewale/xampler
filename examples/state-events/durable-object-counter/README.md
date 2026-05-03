# Durable Objects 07 — Counter

A typed Durable Object counter with `increment`, `get`, and `reset` routes.

## Cloudflare docs

- [Durable Objects](https://developers.cloudflare.com/durable-objects/)

## Copy this API

```python
from xampler.durable_objects import DurableObjectNamespace

namespace = DurableObjectNamespace(env.COUNTERS)
stub = namespace.named("global")
```
