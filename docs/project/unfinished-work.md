# Unfinished and deferred work

This page consolidates deferred work that is currently spread across README and project docs.

## Remote realism and credentials

- Run token-backed prepared profiles with real credentials:
  - Browser Rendering with `CLOUDFLARE_API_TOKEN`.
  - R2 SQL with `WRANGLER_R2_SQL_AUTH_TOKEN`.
  - R2 Data Catalog with `XAMPLER_R2_DATA_CATALOG_TOKEN` or `WRANGLER_R2_SQL_AUTH_TOKEN`.
- Add richer deployed assertions for R2 SQL and R2 Data Catalog row/schema contents.
- Add remote verification for AI Gateway with account, gateway, and provider credentials.
- Add a real Hyperdrive/Postgres verification story.

## API and examples

- Keep expanding per-module API reference pages as APIs mature.
- Add “Copy this API” sections to migrated example READMEs that do not have one yet.
- Consider `xc new <surface>` scaffolding for low-cost examples.
- Add low-cost complex examples from [`complex-example-backlog.md`](complex-example-backlog.md): Email policy router, HTMLRewriter extractor, Workflows timeline, Agents tool calling, and richer Durable Object/WebSocket examples.

## Product coverage gaps

- Cloudflare Images product example.
- Analytics Engine product example.
- Cache-focused example.
- Hyperdrive production example with real Postgres.
- AI Gateway observability/caching/rate-limit metadata.
- Browser Rendering assertions across screenshot/content/PDF/scrape with fixture pages.
- R2 Data Catalog append/read/schema-evolution/snapshot coverage.
- Agents SDK interop beyond deterministic local shape.
- Email Workers and HTMLRewriter reusable library surfaces after additional examples prove the shape.

## Data and streaming caveats

- Python `zipfile` still buffers ZIP bytes because ZIP central directories require seeking.
- HVSC archive extraction still depends on native `7z`/`7zz`; `py7zr` does not support the needed BCJ2 filter.
- Streaming helpers are shared, but more product wrappers should consume them where useful.

## Testability gaps

- Add even deeper direct tests for R2 multipart completion/abort, D1 error paths, Queue tracker integration, Vectorize remote-shaped responses, Browser Rendering response parsing, and R2 Data Catalog schema evolution payloads.
- Add route-level tests for complex apps after the library units are stable.

## Compatibility policy before 0.1

Xampler has not released a stable 0.1 API yet. Prefer one clear import path and one clear method name over compatibility aliases or shims. If a young API needs to change, change it and update examples/tests/docs in the same PR.
