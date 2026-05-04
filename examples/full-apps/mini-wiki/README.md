# Mini Wiki — Workers Assets + D1

A small but usable wiki using one database: D1. Static Assets serve CSS without waking Python; the Worker handles dynamic wiki routes; D1 stores pages, revisions, recent changes, and full-text search.

The app now focuses on the wiki loop: read a page, follow links, create wanted pages, discover backlinks, search, edit with preview, and inspect revision diffs.

## Cloudflare docs

- [Workers](https://developers.cloudflare.com/workers/)
- [Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/)
- [D1](https://developers.cloudflare.com/d1/)
- [Choose a data or storage product](https://developers.cloudflare.com/workers/platform/storage-options/)

## Routes

```text
GET  /                         home page
GET  /all                      all pages
GET  /recent-changes           recent edits
GET  /wanted                   wanted pages from missing links
GET  /wiki/<slug>              render page
GET  /wiki/<slug>/edit         edit form with preview tabs and syntax guide
POST /wiki/<slug>              save revision
GET  /wiki/<slug>/history      revision history with diffs
POST /wiki/<slug>/revert       revert to a previous revision
GET  /wiki/<slug>/raw          raw wiki text
GET  /search?q=...             D1 FTS search with highlighted snippets
GET  /export.jsonl             export revisions

GET  /dev/cached/wiki/<slug>   Cache API wrapper around read-only wiki pages
GET  /dev/events               D1 wide-event observability rows
POST /dev/render               AJAX preview renderer
```

## Wiki syntax

````text
[[Page Name]]        link to a page; missing pages appear in Wanted
WikiWords           still auto-link for classic wiki feel
# Heading
## Subheading
- list item
``` fenced code blocks
````

## Copy this API

```python
from xampler.d1 import D1Database

db = D1Database(env.DB)
page = await db.query_one("SELECT * FROM pages WHERE slug = ?", "home-page")
```

## Local verification

The verifier initializes local D1 from `db_init.sql`, checks seeded pages, backlinks, wanted pages, AJAX preview, edit/save, highlighted search, revision diff history, `/dev/*` observability/cache routes, export, and static CSS served by Assets.
