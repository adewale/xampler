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

## Recommended path

1. Start with [`examples/start/hello-worker/`](examples/start/hello-worker) for the smallest Python Worker.
2. Then use [`examples/storage-data/r2-object-storage/`](examples/storage-data/r2-object-storage) as the first serious primitive: it writes text, uploads a JPEG, streams it back, and byte-compares it.
3. Use [`examples/streaming/gutenberg-stream-composition/`](examples/streaming/gutenberg-stream-composition) to see R2 bytes become D1 full-text-search rows.
4. Use [`examples/state-events/durable-object-chatroom/`](examples/state-events/durable-object-chatroom) to understand stateful coordination and WebSocket broadcast.
5. Use [`examples/network-edge/service-bindings-rpc/`](examples/network-edge/service-bindings-rpc) to see TypeScript and Python Workers interact through real Service Bindings RPC.

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
| [`examples/streaming/gutenberg-stream-composition/`](examples/streaming/gutenberg-stream-composition) | Streaming composition | Gutenberg golden file, byte/text/line/record streams, batches, checkpoints, D1 FTS indexing, AI/agent/WebSocket events. |
| [`examples/network-edge/htmlrewriter-opengraph/`](examples/network-edge/htmlrewriter-opengraph) | HTMLRewriter | OpenGraph metadata model and edge HTML response shape. |
| [`examples/streaming/binary-response/`](examples/streaming/binary-response) | Binary responses | Dependency-free PNG bytes from a Worker. |
| [`examples/network-edge/service-bindings-rpc/`](examples/network-edge/service-bindings-rpc) | Service bindings / RPC | Python RPC service shape with TypeScript client scaffold. |
| [`examples/network-edge/outbound-websocket-consumer/`](examples/network-edge/outbound-websocket-consumer) | WebSockets | WebSocket example scaffold and session model direction. |
| [`examples/state-events/durable-object-chatroom/`](examples/state-events/durable-object-chatroom) | Durable Objects + WebSockets | Chatroom durable object scaffold. |

## Composable API surface

The target shape is small Python wrappers that compose like normal async Python: R2 produces bytes, stream helpers turn bytes into records, batches go to D1/Queues/Vectorize, and AI/Agents/WebSockets can consume or emit typed events.

```python
bucket = R2Bucket(env.ARTIFACTS)
db = D1Database(env.DB)
queue = QueueService(env.JOBS)

stream = await bucket.object("gutenberg/100/raw/pg100-h.zip").byte_stream()
async for batch in aiter_batches(JsonlReader(stream).records(), size=500):
    await db.batch_run([...])
    await queue.send(QueueJob("indexed-batch", {"rows": len(batch)}))

summary = await AIService(env.AI).generate_text(TextGenerationRequest("summarize batch"))
print(summary.text)
```

Real examples include product-specific parsing and SQL details, but the compositional pieces exist today:

- [`examples/storage-data/r2-object-storage`](examples/storage-data/r2-object-storage) is the best post-Hello-World example because it exercises real local object storage with text, binary upload, streaming download, and byte comparison.
- [`examples/streaming/gutenberg-stream-composition`](examples/streaming/gutenberg-stream-composition) reads a real R2 ZIP body stream, unzips it, models byte/text/line/record streams, batches, checkpoints, feeds extracted lines into a checkpointed D1 pipeline, indexes the full text into D1 FTS, and includes AI chunks, agent events, and WebSocket events.
- [`examples/network-edge/service-bindings-rpc`](examples/network-edge/service-bindings-rpc) deploys a Python provider and a TypeScript consumer so cross-language Workers can interact through real Service Bindings RPC.
- [`examples/state-events/durable-object-chatroom`](examples/state-events/durable-object-chatroom) demonstrates Durable Object state plus local and deployed two-client WebSocket broadcast verification.
- [`examples/full-apps/hvsc-ai-data-search`](examples/full-apps/hvsc-ai-data-search) composes R2 datasets, D1 ingestion state/search, Queue-style jobs, Workers AI, and Vectorize seams into an interactive app.
- [`examples/state-events/queues-producer-consumer`](examples/state-events/queues-producer-consumer) and [`examples/ai-agents/agents-sdk-tools`](examples/ai-agents/agents-sdk-tools) show typed jobs and durable sessions/tools.

Reusable wrapper ideas across examples follow one documented vocabulary:

```text
Service → Ref → Request/Options → Result → Event/Handler → Stream/Page/Batch → Status → Policy → Demo → Raw
```

See [`docs/api/vocabulary.md`](docs/api/vocabulary.md) for the full mapping across Cloudflare Developer Platform products.

## Categories

See [`docs/project/example-categories.md`](docs/project/example-categories.md) for the full categorization. Short version:

- **Best local/no-lies:** hello Worker, R2, KV, D1, Assets, Pages, Durable Objects, Cron, Queues, WebSockets/chatroom, binary/streaming examples.
- **Deterministic demo seams:** Workers AI, AI Gateway, Vectorize, Workflows, Browser Rendering, Email, R2 SQL, R2 Data Catalog, Hyperdrive, Agents, LangChain, and parts of HVSC.
- **Remote/paid/account-backed:** Workers AI, AI Gateway, Vectorize, Browser Rendering, Hyperdrive, R2 SQL, R2 Data Catalog, Images, Analytics Engine, deployed Queues/DLQ, deployed Service Bindings, deployed WebSockets.
- **Composition:** Gutenberg streaming, HVSC AI/data search, Service Bindings RPC, Durable Object chatroom.

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
| `examples/ai-agents/vectorize-search` | `/demo` verifies vector API shape locally; `xc remote prepare/verify vectorize` can test a deployed account index. |
| `examples/state-events/workflows-pipeline` | `/demo/*` fakes start/status; remote workflow runtime assertions still need deeper coverage. |
| `examples/state-events/queues-producer-consumer` | Producer is real locally; consumer delivery uses a deterministic harness. |
| `examples/network-edge/service-bindings-rpc` | Local two-worker RPC is verified; `xc remote prepare/verify service-bindings` can test deployed cross-worker RPC. |
| `examples/network-edge/outbound-websocket-consumer` | `/demo/status` does not open the public Jetstream socket. |
| `examples/network-edge/browser-rendering-screenshot` | `/demo` returns screenshot metadata; prepared remote verification can test screenshot/content/PDF/scrape through the real API. |
| `examples/network-edge/email-worker-router` | HTTP route verifies policy; it is not a real Email Routing event. |
| `examples/ai-agents/ai-gateway-chat` | `/demo` mimics OpenAI-compatible shape; `xc doctor ai-gateway` shows the credentials needed for a real gateway call. |
| `examples/storage-data/r2-sql` | `/demo` verifies guarded SQL shaping; prepared remote verification can query a seeded table through real R2 SQL. |
| `examples/storage-data/r2-data-catalog` | `/demo` is a fixture catalog; prepared remote verification can call a deployed Worker against a real Iceberg catalog. |
| `examples/storage-data/hyperdrive-postgres` | `/demo` does not connect to Postgres through Hyperdrive. |
| `examples/ai-agents/agents-sdk-tools` | Demonstrates Agents-like shape with Durable Objects; not direct Cloudflare Agents SDK interop yet. |
| `examples/ai-agents/langchain-style-chain` | LCEL-style chain is verified; it is not yet a real LangChain package workload. |
| `examples/full-apps/hvsc-ai-data-search` | R2/D1/Queue paths are real locally, but AI and Vectorize are deterministic seams. |
| `examples/streaming/gutenberg-stream-composition` | `/zip-demo` streams/unzips the real R2 ZIP; `/fts/ingest` indexes the full extracted text into D1 FTS; `/demo` still uses compact sample text for the checkpointed pipeline. |
| `examples/streaming/binary-response` | Binary response is real, but it is not Cloudflare Images product coverage. |

## Pythonic API principles

Start with [`docs/index.md`](docs/index.md). The main user journey is:

1. [`docs/api/vocabulary.md`](docs/api/vocabulary.md) — the canonical vocabulary and Cloudflare product mapping.
2. [`docs/api/library-surface.md`](docs/api/library-surface.md) — importable modules, base classes, and stability.
3. [`docs/api/reference.md`](docs/api/reference.md) — copyable imports and examples.
4. [`docs/api/testability.md`](docs/api/testability.md) — fake bindings, `Demo*` clients, and remote verification.

Then use focused docs as needed:

- [`docs/api/composition-and-operations.md`](docs/api/composition-and-operations.md)
- [`docs/api/unified-api-surface.md`](docs/api/unified-api-surface.md)
- [`docs/api/protocols.md`](docs/api/protocols.md)
- [`docs/api/primitives-api-surface.md`](docs/api/primitives-api-surface.md)
- [`docs/api/primitive-test-realism.md`](docs/api/primitive-test-realism.md)
- [`docs/runtime/python-workers-runtime-guidance.md`](docs/runtime/python-workers-runtime-guidance.md)
- [`docs/runtime/credentials.md`](docs/runtime/credentials.md)
- [`docs/runtime/remote-verification.md`](docs/runtime/remote-verification.md)
- [`docs/runtime/local-path-development.md`](docs/runtime/local-path-development.md)
- [`docs/data/streaming-api.md`](docs/data/streaming-api.md)
- [`docs/project/unfinished-work.md`](docs/project/unfinished-work.md)

Repo-internal audits, lessons, and planning notes live under `docs/project/` and `docs/archive/`; they are useful for maintainers but are not the main user journey.

The short version: services do work, refs name things, requests/options describe inputs, results describe outputs, events go to handlers, streams/pages/batches move many things, status describes long-running work, policies return decisions, demos prove local behavior, and `.raw` exposes the platform.

## Stable shared base layer

Xampler does not try to hide Cloudflare behind a giant SDK, but `xampler.cloudflare` now provides a tiny canonical base vocabulary for examples that need shared shape:

```python
from xampler.cloudflare import CloudflareService, ResourceRef, RestClient
```

- `CloudflareService[T]` — active wrapper around a Worker binding/action facade.
- `ResourceRef[T]` — passive handle to a named resource such as an object key, Durable Object stub, or workflow instance.
- `RestClient[T]` — token/HTTP backed product client when no Python-usable binding path exists.

Product wrappers now live in the shared package instead of living only inside examples. Canonical imports include:

```python
from xampler.r2 import R2Bucket, R2HttpMetadata, R2Range
from xampler.d1 import D1Database
from xampler.kv import KVNamespace
from xampler.queues import QueueJob, QueueService
from xampler.vectorize import VectorIndex, VectorQuery
from xampler.ai import AIService, TextGenerationRequest
from xampler.browser_rendering import BrowserRendering, ScreenshotRequest
from xampler.r2_sql import R2SqlClient, R2SqlQuery
from xampler.r2_data_catalog import R2DataCatalog
from xampler.durable_objects import DurableObjectNamespace, DurableObjectRef
from xampler.workflows import WorkflowService, WorkflowStatus
from xampler.cron import ScheduledEventInfo
from xampler.service_bindings import ServiceBinding
from xampler.websockets import WebSocketStatus
from xampler.agents import AgentSession, AgentMessage
from xampler.ai_gateway import AIGateway, ChatRequest
```

Examples now import stable product wrappers from `xampler/`; example-local code should be route/UI/fixture/verifier glue or product surfaces that are still deliberately experimental.

## CLI and credential DX

Xampler ships one CLI, `xc`:

```bash
xc doctor
xc verify r2
xc remote prepare vectorize
xc remote verify vectorize
xc remote cleanup vectorize
xc dev link
xc list
xc docs r2
xc doctor r2-sql
xc dev restore
```

Remote actions remain opt-in. `xc remote prepare` sets `XAMPLER_RUN_REMOTE=1` and `XAMPLER_PREPARE_REMOTE=1`; cleanup sets `XAMPLER_CLEANUP_REMOTE=1`. See [`docs/runtime/credentials.md`](docs/runtime/credentials.md).

## Primitive metrics

Coverage and Pythonic API scores live in [`docs/api/primitives-api-surface.md`](docs/api/primitives-api-surface.md). Test realism lives in [`docs/api/primitive-test-realism.md`](docs/api/primitive-test-realism.md).

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
uv run pyright -p pyright.examples.json
uv run pytest -q
```

`uv run pyright` checks the shared `xampler/` package. `uv run pyright -p pyright.examples.json` checks a small allowlist of stable example files. The tiny stubs in `typings/` only teach pyright the minimum shape of runtime modules such as `workers.Response`, `WorkerEntrypoint`, and `js.fetch`; they are not a replacement for Cloudflare runtime types and should stay small.

## Known remote-cost profile

Remote checks are opt-in because they can create Cloudflare resources, deploy Workers, and call paid products. Typical maintainer smoke runs are intentionally tiny, but exact pricing depends on your account plan and Cloudflare's current product pricing.

| Profile | What it may create/call | Cost risk |
|---|---|---|
| `workers-ai` | One deployed Worker and one small Workers AI inference. | Usage-based AI cost. |
| `vectorize` | One small Vectorize index, one Worker, one upsert/query smoke. | Usually tiny; index/storage/query pricing may apply. |
| `queues-dlq` | Two Queues, one Worker, several retry/DLQ messages. | Usually tiny; Queue operations may apply. |
| `service-bindings` | Two deployed Workers. | Worker request/deploy usage. |
| `websockets` | One Durable Object/WebSocket Worker. | Worker/Durable Object/WebSocket duration usage. |
| `browser-rendering` | One Worker and one Browser Rendering screenshot. | Browser Rendering usage-based cost. |
| `r2-sql` | R2 bucket/catalog, one Worker, R2 SQL metadata query. | R2/R2 SQL/Data Catalog usage may apply. |
| `r2-data-catalog` | R2 bucket/catalog, one Worker, Iceberg REST calls. | R2/Data Catalog/API usage may apply. |

Use cleanup when done:

```bash
XAMPLER_RUN_REMOTE=1 XAMPLER_CLEANUP_REMOTE=1 \
  uv run python scripts/cleanup_remote_examples.py vectorize
```

Remote verifiers are separate because they can use real Cloudflare resources and cost money. They never run by default. See [`docs/runtime/remote-verification.md`](docs/runtime/remote-verification.md):

```bash
uv run python scripts/verify_remote_examples.py --list
npx --yes wrangler login
XAMPLER_RUN_REMOTE=1 XAMPLER_REMOTE_WORKERS_AI=1 \
  uv run python scripts/verify_remote_examples.py workers-ai

# Some remote profiles can prepare their own Wrangler-managed prerequisites.
XAMPLER_RUN_REMOTE=1 XAMPLER_PREPARE_REMOTE=1 \
  uv run python scripts/prepare_remote_examples.py vectorize
XAMPLER_RUN_REMOTE=1 XAMPLER_REMOTE_VECTORIZE=1 \
  uv run python scripts/verify_remote_examples.py vectorize
```

Run and verify an example locally with `uv` + `pywrangler`:

```bash
uv run python scripts/verify_examples.py --list
uv run python scripts/verify_examples.py examples/start/hello-worker
uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage
```
