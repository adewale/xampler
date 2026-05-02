# Xampler

Python Workers examples for people who know Python and are learning the Cloudflare Developer Platform.

These examples use [`cfboundary`](https://github.com/adewale/cfboundary) where low-level JavaScript/Python conversion matters: `JsProxy` conversion, Python `bytes` to JavaScript `Uint8Array`, JavaScript `null`/`undefined`, and stream handling.

## Folder structure and naming

Examples live under `examples/` by user journey rather than by sequence number. Names use `<product-or-capability>-<hero-use-case>` and avoid numeric ordering.

```text
examples/start/hello-worker/
examples/storage-data/r2-object-storage/
examples/state-events/queues-producer-consumer/
examples/ai-agents/agents-sdk-tools/
examples/streaming/gutenberg-stream-composition/
examples/full-apps/hvsc-ai-data-search/
```

## Examples

| Example | Primitive / topic | What it demonstrates |
|---|---|---|
| [`examples/start/hello-worker/`](examples/start/hello-worker) | Workers | Minimal Python Worker and response helper. |
| [`examples/storage-data/r2-object-storage/`](examples/storage-data/r2-object-storage) | R2 | Pythonic object storage wrapper, metadata, listing, streaming, multipart. |
| [`examples/storage-data/kv-namespace/`](examples/storage-data/kv-namespace) | Workers KV | `KVNamespace`/`KVKey`, text/JSON values, existence, delete, list. |
| [`examples/start/fastapi-worker/`](examples/start/fastapi-worker) | FastAPI on Workers | Python framework shape on Workers. |
| [`examples/storage-data/d1-database/`](examples/storage-data/d1-database) | D1 | Query wrapper, typed rows, D1 null/boundary conversion. |
| [`examples/ai-agents/langchain-style-chain/`](examples/ai-agents/langchain-style-chain) | Python package / LangChain shape | Keeps package orchestration behind a service boundary. |
| [`examples/start/static-assets/`](examples/start/static-assets) | Workers Assets | Serve static files without waking Python. |
| [`examples/state-events/durable-object-counter/`](examples/state-events/durable-object-counter) | Durable Objects | Stateful counter object. |
| [`examples/state-events/cron-trigger/`](examples/state-events/cron-trigger) | Cron triggers | Scheduled handler with job service object. |
| [`examples/ai-agents/workers-ai-inference/`](examples/ai-agents/workers-ai-inference) | Workers AI | Typed request dataclass and AI service wrapper. |
| [`examples/state-events/workflows-pipeline/`](examples/state-events/workflows-pipeline) | Workflows | Workflow entrypoint and instance creation. |
| [`examples/state-events/queues-producer-consumer/`](examples/state-events/queues-producer-consumer) | Queues | Producer/consumer wrapper, typed jobs, ack/retry. |
| [`examples/ai-agents/vectorize-search/`](examples/ai-agents/vectorize-search) | Vectorize | Typed vectors, upsert, query, get, delete, describe. |
| [`examples/network-edge/browser-rendering-screenshot/`](examples/network-edge/browser-rendering-screenshot) | Browser Rendering | REST screenshot client from a Python Worker. |
| [`examples/network-edge/email-worker-router/`](examples/network-edge/email-worker-router) | Email Workers | Inspect, reject, and forward incoming email. |
| [`examples/ai-agents/ai-gateway-chat/`](examples/ai-agents/ai-gateway-chat) | AI Gateway | OpenAI-compatible chat through AI Gateway. |
| [`examples/storage-data/r2-sql/`](examples/storage-data/r2-sql) | R2 SQL | SQL query client wrapper. |
| [`examples/storage-data/r2-data-catalog/`](examples/storage-data/r2-data-catalog) | R2 Data Catalog | Iceberg REST namespace/table client. |
| [`examples/start/pages-functions/`](examples/start/pages-functions) | Pages | Static Pages project with file-based Function. |
| [`examples/full-apps/hvsc-ai-data-search/`](examples/full-apps/hvsc-ai-data-search) | AI/data app | HVSC release ingestion through R2, D1, Queues, Workers AI/Vectorize seams, and search. |
| [`examples/storage-data/hyperdrive-postgres/`](examples/storage-data/hyperdrive-postgres) | Hyperdrive | Typed Postgres query shape through Hyperdrive with deterministic local transport. |
| [`examples/ai-agents/agents-sdk-tools/`](examples/ai-agents/agents-sdk-tools) | Agents SDK | Stateful agent/session shape with tools, Durable Objects, and typed run results. |
| [`examples/streaming/gutenberg-stream-composition/`](examples/streaming/gutenberg-stream-composition) | Streaming composition | Gutenberg golden file, byte/text/line/record streams, batches, checkpoints, AI/agent/WebSocket events. |
| [`examples/network-edge/htmlrewriter-opengraph/`](examples/network-edge/htmlrewriter-opengraph) | HTMLRewriter | OpenGraph metadata model and edge HTML response shape. |
| [`examples/streaming/binary-response/`](examples/streaming/binary-response) | Binary responses | Dependency-free PNG bytes from a Worker. |
| [`examples/network-edge/service-bindings-rpc/`](examples/network-edge/service-bindings-rpc) | Service bindings / RPC | Python RPC service shape with TypeScript client scaffold. |
| [`examples/network-edge/outbound-websocket-consumer/`](examples/network-edge/outbound-websocket-consumer) | WebSockets | WebSocket example scaffold and session model direction. |
| [`examples/state-events/durable-object-chatroom/`](examples/state-events/durable-object-chatroom) | Durable Objects + WebSockets | Chatroom durable object scaffold. |

## Best no-lies examples

These are the best starting points because they do something easy to explain and their verifier exercises the real local Cloudflare primitive path rather than a fake/demo transport.

| Example | Why it is trustworthy |
|---|---|
| [`examples/start/hello-worker/`](examples/start/hello-worker) | Starts a real Python Worker and returns a real response. |
| [`examples/storage-data/r2-object-storage/`](examples/storage-data/r2-object-storage) | Writes text, uploads `BreakingThe35.jpeg`, streams it back, and byte-compares it. |
| [`examples/storage-data/kv-namespace/`](examples/storage-data/kv-namespace) | Uses local KV for text, JSON, list, delete, and missing-key behavior. |
| [`examples/storage-data/d1-database/`](examples/storage-data/d1-database) | Initializes local D1, creates an index, runs real bound queries, and checks `EXPLAIN`. |
| [`examples/start/static-assets/`](examples/start/static-assets) | Proves static assets are served without waking Python; dynamic `/api/status` still runs Python. |
| [`examples/state-events/durable-object-counter/`](examples/state-events/durable-object-counter) | Uses real local Durable Objects and verifies named-object isolation. |
| [`examples/state-events/cron-trigger/`](examples/state-events/cron-trigger) | Hits Wrangler's local scheduled handler endpoint and runs the scheduled job path. |
| [`examples/start/pages-functions/`](examples/start/pages-functions) | Runs `pages dev`, serves static Pages output, and verifies a file-routed Function. |

## Examples with deliberate demo seams

These examples are useful, but they contain a local stand-in, deterministic transport, or partial truth. They are marked this way so the repo does not confuse API-shape verification with real remote product verification.

| Example | The lie / seam |
|---|---|
| `examples/ai-agents/workers-ai-inference` | `/demo` is deterministic; `/` is the real Workers AI binding path. |
| `examples/ai-agents/vectorize-search` | `/demo` verifies vector API shape locally; real Vectorize needs an account index. |
| `examples/state-events/workflows-pipeline` | `/demo/*` fakes start/status; real workflow runtime verification is still needed. |
| `examples/state-events/queues-producer-consumer` | Producer is real locally; consumer delivery uses a deterministic harness. |
| `examples/network-edge/service-bindings-rpc` | Python provider is verified; full two-worker RPC flow is not one-command verified yet. |
| `examples/network-edge/outbound-websocket-consumer` | `/demo/status` does not open the public Jetstream socket. |
| `examples/network-edge/browser-rendering-screenshot` | `/demo` returns screenshot metadata, not a real browser screenshot. |
| `examples/network-edge/email-worker-router` | HTTP route verifies policy; it is not a real Email Routing event. |
| `examples/ai-agents/ai-gateway-chat` | `/demo` mimics OpenAI-compatible shape; real gateway call needs credentials. |
| `examples/storage-data/r2-sql` | `/demo` verifies guarded SQL shaping; real R2 SQL is account-backed. |
| `examples/storage-data/r2-data-catalog` | `/demo` is a fixture catalog; real Iceberg catalog verification is still needed. |
| `examples/storage-data/hyperdrive-postgres` | `/demo` does not connect to Postgres through Hyperdrive. |
| `examples/ai-agents/agents-sdk-tools` | Demonstrates Agents-like shape with Durable Objects; not direct Cloudflare Agents SDK interop yet. |
| `examples/ai-agents/langchain-style-chain` | LCEL-style chain is verified; it is not yet a real LangChain package workload. |
| `examples/full-apps/hvsc-ai-data-search` | R2/D1/Queue paths are real locally, but AI and Vectorize are deterministic seams. |
| `examples/streaming/gutenberg-stream-composition` | Golden zip is real in R2, but `/demo` currently streams sample text instead of unzipping the archive. |
| `examples/streaming/binary-response` | Binary response is real, but it is not Cloudflare Images product coverage. |

## Pythonic API principles

Start with [`docs/index.md`](docs/index.md). The highest-value docs are:

- [`docs/api/unified-api-surface.md`](docs/api/unified-api-surface.md)
- [`docs/api/primitives-api-surface.md`](docs/api/primitives-api-surface.md)
- [`docs/api/primitive-test-realism.md`](docs/api/primitive-test-realism.md)
- [`docs/runtime/python-workers-runtime-guidance.md`](docs/runtime/python-workers-runtime-guidance.md)
- [`docs/data/streaming-api.md`](docs/data/streaming-api.md)
- [`docs/project/original-goals-audit.md`](docs/project/original-goals-audit.md)
- [`docs/project/gaps-explained.md`](docs/project/gaps-explained.md)

The short version:

1. Wrap each Cloudflare binding in a small service object.
2. Use resource handles where that matches Python expectations.
3. Return native Python values and dataclasses.
4. Keep `cfboundary` conversion at the JS/Python boundary.
5. Use `async for` for pagination/streams and `async with` for lifecycles.
6. Keep `.raw` as an explicit escape hatch.

## Primitive metrics

Coverage and Pythonic API scores are out of 10. Test realism is out of 5; see [`docs/api/primitive-test-realism.md`](docs/api/primitive-test-realism.md).

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
uv run pyright
uv run pytest -q
```

Run and verify an example locally with `uv` + `pywrangler`:

```bash
uv run python scripts/verify_examples.py --list
uv run python scripts/verify_examples.py examples/start/hello-worker
uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage
```
