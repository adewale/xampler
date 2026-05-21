# Unfinished and deferred work

This page consolidates deferred work that is currently spread across README and project docs.

## Files SDK-inspired DX baseline

The `files-sdk.dev` comparison produced a baseline that is now reflected in code and docs:

- [`../api/capabilities.md`](../api/capabilities.md) labels operations as **supported**, **caveated**, **demo-only**, **remote-only**, **unsupported/throws**, or **not covered**.
- [`../api/reference/r2.md`](../api/reference/r2.md) documents public URL, signed URL, CORS, content-type, direct-upload, `Content-Disposition`, and streaming/memory caveats.
- `xampler.errors.XamplerError` provides normalized non-absence failures: `not_found`, `unauthorized`, `conflict`, `bad_request`, `unsupported`, and `provider` while preserving `cause`.
- Runtime-only `js` imports in REST-backed clients are guarded/lazy instead of imported at module import time.
- `xampler.agent_tools.create_r2_object_tools()` provides SDK-neutral read/write tools with approval-gated mutations and `read_only=True`.
- `xc` now has noun/action groups (`examples list`, `examples verify`, `docs path`, `remote plan`) without compatibility aliases.
- `xc --json list`, `xc --json doctor`, global `--dry-run`, `--quiet`, `--verbose`, and `xc remote plan <profile> --json` provide a machine-readable automation baseline.
- `xampler.cli.CommandPlan`, `Surface`, and the central `SURFACES` registry keep command implementation composable.
- Committed CLI fuzz/property tests cover random argv inputs, the exhaustive valid surface matrix, JSON invariants, and removed aliases.
- Remote verifiers for Browser Rendering, R2 SQL, R2 Data Catalog, and AI Gateway now assert more than substrings: response headers, byte sizes, JSON shape, echoed SQL, and lifecycle/table payloads.
- The experimental `ty` run has been converted into low-risk cleanups while `pyright` remains the gating checker.

Future polish should extend these patterns to more primitives rather than inventing new conventions.

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
