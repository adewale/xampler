# Queues 16 — Producer and Consumer

Run with `uv run pywrangler dev`. POST JSON to `/jobs`; consume locally with Wrangler queue tooling when available.

## Cloudflare docs

- [Queues](https://developers.cloudflare.com/queues/)

## Copy this API

```python
from xampler.queues import QueueJob, QueueService

queue = QueueService(env.JOBS)
await queue.send(QueueJob("resize", {"image": "r2://bucket/key.jpg"}))
```
