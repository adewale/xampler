# Mini Wiki — Workers Assets + D1

A minimal Instiki-style wiki using one database: D1. Static Assets serve CSS without waking Python; the Worker handles dynamic wiki routes; D1 stores pages, revisions, recent changes, and full-text search.

## Cloudflare docs

- [Workers](https://developers.cloudflare.com/workers/)
- [Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/)
- [D1](https://developers.cloudflare.com/d1/)
- [Choose a data or storage product](https://developers.cloudflare.com/workers/platform/storage-options/)

## Routes

```text
GET  /                    recent pages
GET  /wiki/<slug>          render page
GET  /wiki/<slug>/edit     edit form
POST /wiki/<slug>          save revision
GET  /wiki/<slug>/history  revision history
GET  /wiki/<slug>/raw      raw wiki text
GET  /search?q=...         D1 FTS search
GET  /export.jsonl         export revisions
```

## Copy this API

```python
from xampler.d1 import D1Database

db = D1Database(env.DB)
page = await db.query_one("SELECT * FROM pages WHERE slug = ?", "HomePage")
```

## Local verification

The verifier initializes local D1 from `db_init.sql`, starts the Worker, creates and edits a page, checks history/raw/search, and verifies static CSS is served by Assets.
