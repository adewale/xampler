# D1 04 — Query

Pythonic D1 wrapper: typed rows, `query`, `query_one`, and boundary conversion.

## Cloudflare docs

- [D1](https://developers.cloudflare.com/d1/)

## Copy this API

```python
from xampler.d1 import D1Database

db = D1Database(env.DB)
row = await db.query_one("SELECT quote, author FROM quotes LIMIT 1")
```
