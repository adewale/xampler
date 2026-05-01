# Primitive Test Realism Matrix

Last reviewed: 2026-05-01.

This document tracks how realistically each Cloudflare primitive example is tested. It separates three things that are easy to conflate:

1. **Static validation** — Python code parses, lints, and unit tests pass.
2. **Local runtime verification** — `uv run pywrangler dev` is started and HTTP/WebSocket/email/queue behavior is exercised. Pages is the exception because Pages Functions are not Python Workers.
3. **Cloudflare resource realism** — the example uses the real primitive semantics, not just an in-memory stand-in.

## Realism levels

| Level | Meaning |
|---:|---|
| 0 | Not tested. |
| 1 | Static only: lint/import/unit tests, no Worker runtime. |
| 2 | Worker starts locally, but only a shallow route/health check is verified. |
| 3 | Local runtime exercises the primitive with local Wrangler/Miniflare semantics. |
| 4 | Local runtime exercises the primitive including realistic data and edge cases. |
| 5 | Deployed or remote-binding verification against real Cloudflare infrastructure. |

## Matrix

| Primitive | Example | Realism | Current verification | What is actually tested | Main gap to next level |
|---|---|---:|---|---|---|
| Workers request/response | `workers-01-hello` | 3 | `uv run python scripts/verify_examples.py workers-01-hello` | Starts Python Worker locally and checks HTTP response body. | Add multiple methods/headers/error response checks. |
| R2 object storage | `r2-01` | 4 | `uv run python scripts/verify_examples.py r2-01` | Starts Worker locally, writes/reads text, uploads `fixtures/BreakingThe35.jpeg`, streams it back, byte-compares download. | Remote-binding/deployed R2 verification; multipart verification. |
| Workers KV | `kv-02-binding` | 3 | `uv run python scripts/verify_examples.py kv-02-binding` | Starts Worker locally, writes text to KV, reads it back. | Verify JSON, TTL, delete, list/iteration, deployed KV namespace. |
| FastAPI / ASGI | `fastapi-03-framework` | 1 | Static validation only. | Code parses/lints; ASGI bridge is implemented. | Add verifier checks for `/`, `/items/python`, `/env`. |
| D1 database | `d1-04-query` | 1 | Static validation only. | Code parses/lints; query wrapper tested indirectly by syntax only. | Automate local `wrangler d1 execute --file db_init.sql`, then verify query route. |
| LangChain/package orchestration | `ai-05-langchain` | 1 | Static validation only. | Service-boundary placeholder parses/lints. | Replace with real LangChain-compatible workload or remove. |
| Workers Assets | `assets-06-static-assets` | 3 | `uv run python scripts/verify_examples.py assets-06-static-assets` | Starts Worker locally and verifies the static asset is served by Workers Assets instead of Python. | Also verify a dynamic Python route under a non-asset path. |
| Durable Objects | `durable-objects-07-counter` | 3 | `uv run python scripts/verify_examples.py durable-objects-07-counter` | Starts Worker locally, resets counter, increments, reads persisted DO state. | Verify concurrent increments and named-object isolation. |
| Cron Triggers | `scheduled-08-cron` | 2 | `uv run python scripts/verify_examples.py scheduled-08-cron` | Starts Worker locally and verifies the HTTP health route. | Hit local scheduled endpoint `/cdn-cgi/handler/scheduled?...` and assert logs/side effects. |
| Workers AI | `workers-ai-09-inference` | 1 | Static validation only. | Wrapper and typed request parse/lint. | Verify local/deployed AI binding call with deterministic prompt or mocked model. |
| Workflows | `workflows-10-pipeline` | 1 | Static validation only. | Workflow class and service wrapper parse/lint. | Start workflow locally/deployed, poll `/status/<id>`. |
| Queues | `queues-16-producer-consumer` | 1 | Static validation only. | Producer/consumer code parses/lints. | Verify enqueue route and local queue consumer processing/ack behavior. |
| Vectorize | `vectorize-17-search` | 1 | Static validation only. | Typed vector/query wrapper parses/lints. | Create local/remote index, upsert vector, query it, verify match. |
| HTMLRewriter | `htmlrewriter-11-opengraph` | 2 | `uv run python scripts/verify_examples.py htmlrewriter-11-opengraph` | Starts Worker locally and verifies OpenGraph HTML output. | Use real HTMLRewriter and verify injected tags in response. |
| Images / binary responses | `images-12-generation` | 3 | `uv run python scripts/verify_examples.py images-12-generation` | Starts Worker locally and verifies a generated PNG response path. | Verify content-type and PNG signature explicitly. |
| Service bindings / RPC | `service-bindings-13-rpc` | 1 | Static validation only. | Python service and TS client files exist/parse partially. | One-command two-process verifier: start Python service, start TS client, verify highlighted HTML. |
| Outbound WebSockets | `websockets-14-stream-consumer` | 1 | Static validation only. | Durable Object/WebSocket code parses/lints. | Start Worker and verify `/status`; add deterministic fake WebSocket server if possible. |
| Durable Objects + WebSockets | `durable-objects-15-chatroom` | 1 | Static validation only. | Chatroom page and DO code parse/lint. | Automated WebSocket client sends message and verifies broadcast. |
| Browser Rendering | `browser-rendering-18-screenshot` | 1 | Static validation only. | REST client wrapper parses/lints. | Verify against real Browser Rendering API with token or provide fake endpoint mode. |
| Email Workers | `email-workers-19-router` | 1 | Static validation only. | Email handler parses/lints. | Add local email event harness or deployed Email Routing test. |
| AI Gateway | `ai-gateway-20-universal` | 1 | Static validation only. | Gateway client parses/lints. | Verify with test gateway/provider key; assert response shape and gateway metadata. |
| R2 SQL | `r2-sql-21-query` | 1 | Static validation only. | SQL client parses/lints. | Verify against real R2 SQL endpoint with `SHOW DATABASES` and sample query. |
| R2 Data Catalog | `r2-data-catalog-22-iceberg` | 1 | Static validation only. | Iceberg REST client parses/lints. | Verify namespace/table listing against real catalog; add PyIceberg client example. |
| Pages | `pages-23-functions` | 1 | Static validation only. | Pages files exist; TS function not yet runtime-verified. | Run `npx wrangler pages dev public` and verify `/` plus `/api/hello?name=Python`. |

## Current realism summary

| Level | Count | Examples |
|---:|---:|---|
| 4 | 1 | `r2-01` |
| 3 | 5 | `workers-01-hello`, `kv-02-binding`, `assets-06-static-assets`, `durable-objects-07-counter`, `images-12-generation` |
| 2 | 2 | `scheduled-08-cron`, `htmlrewriter-11-opengraph` |
| 1 | 16 | all remaining examples |
| 0 | 0 | — |

## Highest-priority testing work

1. **Make every example at least level 2**: prove the Worker or Pages project starts and responds locally.
2. **Bring D1, Assets, Images, FastAPI, Pages to level 3 quickly**: these should be straightforward local smoke tests.
3. **Bring Queues, Chatroom WebSockets, Service Bindings to level 3/4**: requires multi-step local harnesses.
4. **Bring Browser Rendering, AI Gateway, R2 SQL, R2 Data Catalog to level 5**: these depend on real Cloudflare account resources and tokens.
5. **Keep R2 at level 4+**: the JPEG byte-for-byte upload/download fixture is the current gold standard for realistic local verification.

## Verification commands currently known to pass

```bash
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
uv run python scripts/verify_examples.py kv-02-binding
uv run python scripts/verify_examples.py durable-objects-07-counter
uv run python scripts/verify_examples.py assets-06-static-assets
uv run python scripts/verify_examples.py images-12-generation
uv run python scripts/verify_examples.py htmlrewriter-11-opengraph
uv run python scripts/verify_examples.py scheduled-08-cron
```
