# Xampler

Python Workers examples for people who know Python and are learning the Cloudflare Developer Platform.

These examples use [`cfboundary`](https://github.com/adewale/cfboundary) where low-level JavaScript/Python conversion matters: `JsProxy` conversion, Python `bytes` to JavaScript `Uint8Array`, JavaScript `null`/`undefined`, and stream handling.

## Naming convention

Example directories put the Cloudflare product or primitive first, then the number:

```text
r2-01/
kv-02-binding/
d1-04-query/
```

## Examples

| Example | Primitive / topic | What it demonstrates |
|---|---|---|
| [`workers-01-hello/`](workers-01-hello) | Workers | Minimal Python Worker and response helper. |
| [`r2-01/`](r2-01) | R2 | Pythonic object storage wrapper, metadata, listing, streaming, multipart. |
| [`kv-02-binding/`](kv-02-binding) | Workers KV | `KVNamespace`/`KVKey`, text/JSON values, existence, delete, list. |
| [`fastapi-03-framework/`](fastapi-03-framework) | FastAPI on Workers | Python framework shape on Workers. |
| [`d1-04-query/`](d1-04-query) | D1 | Query wrapper, typed rows, D1 null/boundary conversion. |
| [`ai-05-langchain/`](ai-05-langchain) | Python package / LangChain shape | Keeps package orchestration behind a service boundary. |
| [`assets-06-static-assets/`](assets-06-static-assets) | Workers Assets | Serve static files without waking Python. |
| [`durable-objects-07-counter/`](durable-objects-07-counter) | Durable Objects | Stateful counter object. |
| [`scheduled-08-cron/`](scheduled-08-cron) | Cron triggers | Scheduled handler with job service object. |
| [`workers-ai-09-inference/`](workers-ai-09-inference) | Workers AI | Typed request dataclass and AI service wrapper. |
| [`workflows-10-pipeline/`](workflows-10-pipeline) | Workflows | Workflow entrypoint and instance creation. |
| [`queues-16-producer-consumer/`](queues-16-producer-consumer) | Queues | Producer/consumer wrapper, typed jobs, ack/retry. |
| [`vectorize-17-search/`](vectorize-17-search) | Vectorize | Typed vectors, upsert, query, get, delete, describe. |
| [`browser-rendering-18-screenshot/`](browser-rendering-18-screenshot) | Browser Rendering | REST screenshot client from a Python Worker. |
| [`email-workers-19-router/`](email-workers-19-router) | Email Workers | Inspect, reject, and forward incoming email. |
| [`ai-gateway-20-universal/`](ai-gateway-20-universal) | AI Gateway | OpenAI-compatible chat through AI Gateway. |
| [`r2-sql-21-query/`](r2-sql-21-query) | R2 SQL | SQL query client wrapper. |
| [`r2-data-catalog-22-iceberg/`](r2-data-catalog-22-iceberg) | R2 Data Catalog | Iceberg REST namespace/table client. |
| [`pages-23-functions/`](pages-23-functions) | Pages | Static Pages project with file-based Function. |
| [`hvsc-24-ai-data-search/`](hvsc-24-ai-data-search) | AI/data app | HVSC release ingestion through R2, D1, Queues, Workers AI/Vectorize seams, and search. |
| [`hyperdrive-25-postgres/`](hyperdrive-25-postgres) | Hyperdrive | Typed Postgres query shape through Hyperdrive with deterministic local transport. |
| [`agents-26-sdk/`](agents-26-sdk) | Agents SDK | Stateful agent/session shape with tools, Durable Objects, and typed run results. |
| [`streaming-27-gutenberg/`](streaming-27-gutenberg) | Streaming composition | Gutenberg golden file, byte/text/line/record streams, batches, checkpoints, AI/agent/WebSocket events. |
| [`htmlrewriter-11-opengraph/`](htmlrewriter-11-opengraph) | HTMLRewriter | OpenGraph metadata model and edge HTML response shape. |
| [`images-12-generation/`](images-12-generation) | Binary responses | Dependency-free PNG bytes from a Worker. |
| [`service-bindings-13-rpc/`](service-bindings-13-rpc) | Service bindings / RPC | Python RPC service shape with TypeScript client scaffold. |
| [`websockets-14-stream-consumer/`](websockets-14-stream-consumer) | WebSockets | WebSocket example scaffold and session model direction. |
| [`durable-objects-15-chatroom/`](durable-objects-15-chatroom) | Durable Objects + WebSockets | Chatroom durable object scaffold. |

## Best no-lies examples

These are the best starting points because they do something easy to explain and their verifier exercises the real local Cloudflare primitive path rather than a fake/demo transport.

| Example | Why it is trustworthy |
|---|---|
| [`workers-01-hello/`](workers-01-hello) | Starts a real Python Worker and returns a real response. |
| [`r2-01/`](r2-01) | Writes text, uploads `BreakingThe35.jpeg`, streams it back, and byte-compares it. |
| [`kv-02-binding/`](kv-02-binding) | Uses local KV for text, JSON, list, delete, and missing-key behavior. |
| [`d1-04-query/`](d1-04-query) | Initializes local D1, creates an index, runs real bound queries, and checks `EXPLAIN`. |
| [`assets-06-static-assets/`](assets-06-static-assets) | Proves static assets are served without waking Python; dynamic `/api/status` still runs Python. |
| [`durable-objects-07-counter/`](durable-objects-07-counter) | Uses real local Durable Objects and verifies named-object isolation. |
| [`scheduled-08-cron/`](scheduled-08-cron) | Hits Wrangler's local scheduled handler endpoint and runs the scheduled job path. |
| [`pages-23-functions/`](pages-23-functions) | Runs `pages dev`, serves static Pages output, and verifies a file-routed Function. |

## Examples with deliberate demo seams

These examples are useful, but they contain a local stand-in, deterministic transport, or partial truth. They are marked this way so the repo does not confuse API-shape verification with real remote product verification.

| Example | The lie / seam |
|---|---|
| `workers-ai-09-inference` | `/demo` is deterministic; `/` is the real Workers AI binding path. |
| `vectorize-17-search` | `/demo` verifies vector API shape locally; real Vectorize needs an account index. |
| `workflows-10-pipeline` | `/demo/*` fakes start/status; real workflow runtime verification is still needed. |
| `queues-16-producer-consumer` | Producer is real locally; consumer delivery uses a deterministic harness. |
| `service-bindings-13-rpc` | Python provider is verified; full two-worker RPC flow is not one-command verified yet. |
| `websockets-14-stream-consumer` | `/demo/status` does not open the public Jetstream socket. |
| `browser-rendering-18-screenshot` | `/demo` returns screenshot metadata, not a real browser screenshot. |
| `email-workers-19-router` | HTTP route verifies policy; it is not a real Email Routing event. |
| `ai-gateway-20-universal` | `/demo` mimics OpenAI-compatible shape; real gateway call needs credentials. |
| `r2-sql-21-query` | `/demo` verifies guarded SQL shaping; real R2 SQL is account-backed. |
| `r2-data-catalog-22-iceberg` | `/demo` is a fixture catalog; real Iceberg catalog verification is still needed. |
| `hyperdrive-25-postgres` | `/demo` does not connect to Postgres through Hyperdrive. |
| `agents-26-sdk` | Demonstrates Agents-like shape with Durable Objects; not direct Cloudflare Agents SDK interop yet. |
| `ai-05-langchain` | LCEL-style chain is verified; it is not yet a real LangChain package workload. |
| `hvsc-24-ai-data-search` | R2/D1/Queue paths are real locally, but AI and Vectorize are deterministic seams. |
| `streaming-27-gutenberg` | Golden zip is real in R2, but `/demo` currently streams sample text instead of unzipping the archive. |
| `images-12-generation` | Binary response is real, but it is not Cloudflare Images product coverage. |

## Pythonic API principles

See:

- [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md)
- [`docs/pythonic-rubric.md`](docs/pythonic-rubric.md)
- [`docs/cloudflare-python-api-shape.md`](docs/cloudflare-python-api-shape.md)
- [`docs/s3-python-library-research.md`](docs/s3-python-library-research.md)
- [`docs/api-iteration-log.md`](docs/api-iteration-log.md)
- [`docs/api-surface-review.md`](docs/api-surface-review.md)
- [`docs/unified-api-surface.md`](docs/unified-api-surface.md)
- [`docs/primitives-api-surface.md`](docs/primitives-api-surface.md)
- [`docs/python-design-patterns.md`](docs/python-design-patterns.md)
- [`docs/top-10-improvement-plan.md`](docs/top-10-improvement-plan.md)
- [`docs/primitive-test-realism.md`](docs/primitive-test-realism.md)
- [`docs/pythonic-tooling.md`](docs/pythonic-tooling.md)
- [`docs/python-workers-runtime-guidance.md`](docs/python-workers-runtime-guidance.md)
- [`docs/streaming-api.md`](docs/streaming-api.md)
- [`docs/native-python-workers-comparison.md`](docs/native-python-workers-comparison.md)
- [`docs/project-structure-and-naming.md`](docs/project-structure-and-naming.md)
- [`docs/cloudflare-doc-links.md`](docs/cloudflare-doc-links.md)
- [`docs/wrapper-consistency-audit.md`](docs/wrapper-consistency-audit.md)
- [`docs/datasets.md`](docs/datasets.md)
- [`docs/dataset-reuse-coverage.md`](docs/dataset-reuse-coverage.md)
- [`docs/cloudflare-best-practices-alignment.md`](docs/cloudflare-best-practices-alignment.md)
- [`docs/cloudflare-primitives-pythonic-scores.md`](docs/cloudflare-primitives-pythonic-scores.md)
- [`docs/example-rubric-scores.md`](docs/example-rubric-scores.md)
- [`docs/examples-status-and-pythonicness.md`](docs/examples-status-and-pythonicness.md)
- [`docs/executable-examples.md`](docs/executable-examples.md)
- [`docs/tier-1-completion-plan.md`](docs/tier-1-completion-plan.md)
- [`docs/composite-example-backlog.md`](docs/composite-example-backlog.md)

The short version:

1. Wrap each Cloudflare binding in a small service object.
2. Use resource handles where that matches Python expectations.
3. Return native Python values and dataclasses.
4. Keep `cfboundary` conversion at the JS/Python boundary.
5. Use `async for` for pagination/streams and `async with` for lifecycles.
6. Keep `.raw` as an explicit escape hatch.

## Primitive metrics

Coverage and Pythonic API scores are out of 10. Test realism is out of 5; see [`docs/primitive-test-realism.md`](docs/primitive-test-realism.md).

| Tier | Primitive | Coverage / 10 | Pythonic API / 10 | Test Realism / 5 |
|---|---|---:|---:|---:|
| Tier 1 — Gold standard | R2 object storage | 8.5 | 9.25 | 4 |
| Tier 1 — Gold standard | Workers KV | 8.0 | 8.8 | 4 |
| Tier 1 — Gold standard | Durable Objects | 7.0 | 8.6 | 4 |
| Tier 1 — Gold standard | Workers Assets | 7.4 | 9.0 | 4 |
| Tier 1 — Gold standard | D1 database | 7.5 | 8.9 | 4 |
| Tier 1 — Gold standard | Binary responses | 6.0 | 8.2 | 4 |
| Tier 1 — Gold standard | Cron Triggers | 6.5 | 8.5 | 4 |
| Tier 1 — Gold standard | HTMLRewriter | 5.5 | 8.3 | 4 |
| Tier 1 — Gold standard | Queues | 8.1 | 8.7 | 4 |
| Tier 1 — Gold standard | FastAPI / ASGI | 6.0 | 8.0 | 3 |
| Tier 1 — Gold standard | Workers AI | 6.3 | 8.7 | 4 |
| Tier 1 — Gold standard | Vectorize | 7.8 | 8.7 | 4 |
| Tier 1 — Gold standard | Durable Objects + WebSockets | 7.5 | 8.5 | 4 |
| Tier 1 — Gold standard | Pages | 6.0 | 8.4 | 4 |
| Tier 1 — Gold standard | Workflows | 7.2 | 8.5 | 4 |
| Tier 1 — Gold standard | R2 SQL | 6.5 | 8.4 | 4 |
| Tier 1 — Gold standard | HVSC AI/data app | 8.6 | 9.0 | 4.5 |
| Tier 1 — Gold standard | Service Bindings / RPC | 6.8 | 8.3 | 3 |
| Tier 1 — Gold standard | Outbound WebSockets | 7.0 | 8.2 | 3 |
| Tier 1 — Gold standard | Browser Rendering | 6.2 | 8.2 | 3 |
| Tier 1 — Gold standard | Email Workers | 6.5 | 8.3 | 3 |
| Tier 1 — Gold standard | AI Gateway | 6.5 | 8.4 | 3 |
| Tier 1 — Gold standard | R2 Data Catalog | 6.8 | 8.3 | 3 |
| Tier 1 — Gold standard | LangChain/package orchestration | 6.2 | 8.1 | 3 |
| Tier 1 — Gold standard | Hyperdrive | 6.5 | 8.4 | 3 |
| Tier 1 — Gold standard | Agents SDK | 6.8 | 8.6 | 3 |
| Tier 1 — Gold standard | Streaming composition | 7.2 | 8.8 | 3 |

## Requirements

- Python 3.13+
- `uv` for dependency management, local Worker runs, checks, and tests
- Node.js available on PATH because Wrangler is a JavaScript tool under the hood
- A Cloudflare account for deployed resources

Python Workers are configured with the `python_workers` compatibility flag.

## Running checks

Static/local Python checks:

```bash
uv sync
uv run ruff check .
uv run pytest -q
```

Run and verify an example locally with `uv` + `pywrangler`:

```bash
uv run python scripts/verify_examples.py --list
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
```
