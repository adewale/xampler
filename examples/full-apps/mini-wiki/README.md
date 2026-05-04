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

## Backlinks with D1

The current example computes backlinks by scanning page bodies in Python. For a larger D1 wiki, make links relational:

```sql
CREATE TABLE page_links (
  from_slug TEXT NOT NULL,
  to_slug TEXT NOT NULL,
  label TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (from_slug, to_slug, label)
);

CREATE INDEX idx_page_links_to_slug ON page_links(to_slug);
```

On every save, parse `[[Page Name]]`/WikiWord links, delete old rows for `from_slug`, and insert the new outbound links in the same logical save flow. Then backlinks are cheap:

```sql
SELECT p.slug, p.title, p.current_revision, p.updated_at
FROM page_links l
JOIN pages p ON p.slug = l.from_slug
WHERE l.to_slug = ?
ORDER BY p.updated_at DESC;
```

Wanted pages are the inverse:

```sql
SELECT l.to_slug, COUNT(*) AS link_count
FROM page_links l
LEFT JOIN pages p ON p.slug = l.to_slug
WHERE p.slug IS NULL
GROUP BY l.to_slug
ORDER BY link_count DESC, l.to_slug;
```

## Copy this API

```python
from xampler.d1 import D1Database

db = D1Database(env.DB)
page = await db.query_one("SELECT * FROM pages WHERE slug = ?", "home-page")
```

## Local verification

The verifier initializes local D1 from `db_init.sql`, checks seeded pages, backlinks, wanted pages, AJAX preview, edit/save, highlighted search, revision diff history, `/dev/*` observability/cache routes, export, and static CSS served by Assets.
