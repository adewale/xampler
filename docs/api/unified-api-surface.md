# Unified Pythonic API Surface

Last reviewed: 2026-05-02.

The examples converge on one shape: Cloudflare bindings become small services, named resources become handles, inputs/results are dataclasses, long-running work exposes status, and every wrapper keeps `.raw` for platform escape hatches.

```python
# Bindings become services.
r2 = R2Bucket(env.BUCKET)
kv = KVNamespace(env.KV)
db = D1Database(env.DB)
queue = QueueService(env.QUEUE)
ai = AIService(env.AI)
agent = AgentSession(env.AGENT)

# Named things become handles.
obj = r2.object("datasets/hvsc/tracks.jsonl")
key = kv.key("profile:ada")
stmt = db.statement("SELECT * FROM tracks WHERE search_text LIKE ?")
run = workflows.instance("import-123")

# Inputs/results are dataclasses.
await obj.write_json(Track(...))
track = await stmt.one_as(Track, "%hubbard%")
await queue.send(IngestJob(...))
result: AgentRunResult = await agent.run("summarize jeroen tel tracks")

# Python protocols are preferred.
async for item in r2.iter_objects(prefix="datasets/"):
    ...

async with r2.multipart("large.bin") as upload:
    await upload.part(1, chunk)

# Long-running work exposes status.
status = await run.status()
progress = await pipeline.ingest_status()

# Escape hatch remains explicit.
raw = r2.raw
```

## Stable shared base layer

The tiny canonical base vocabulary lives in `xampler.cloudflare`:

```python
from xampler.cloudflare import CloudflareService, ResourceRef, RestClient
```

- `CloudflareService[T]` is for active Worker binding/action facades.
- `ResourceRef[T]` is for passive handles to named resources.
- `RestClient[T]` is for token/HTTP backed product APIs.

These classes intentionally only store `raw`/`name`/`base_url`; they are not a giant SDK façade. R2 is the first product wrapper promoted into the shared package:

```python
from xampler.r2 import R2Bucket, R2ObjectRef, R2HttpMetadata, R2Range
```

Other product-specific tutorial wrappers stay in examples until their shape proves reusable.

## Reused concepts

The API surface is deliberately small. A few concepts repeat across products so examples compose instead of becoming unrelated wrappers.

| Concept | Reused as | Why it composes |
|---|---|---|
| Service wrapper | `R2Bucket`, `D1Database`, `QueueService`, `AIService`, `VectorIndex`, `HyperdrivePostgres` | One object owns the binding/client and boundary conversion. |
| Resource handle | `bucket.object(key)`, `kv.key(name)`, `workflow.instance(id)`, `room("name")` | Handles are cheap, passable references with domain verbs. |
| Dataclass input | `QueueJob`, `VectorQuery`, `TextGenerationRequest`, `PostgresQuery`, `AgentMessage` | A typed result from one primitive can become another primitive's input. |
| Dataclass result/status | `VectorQueryResult`, `WorkflowStatus`, `StreamCheckpoint`, `AgentRunResult` | Long-running and composed flows can report state without raw dictionaries. |
| Async iteration | `iter_objects`, `iter_keys`, `iter_lines`, `AgentSession.stream()` | Streams and pagination use Python's native `async for` shape. |
| Context manager | R2 multipart upload | Lifecycle-bound work uses `async with` for cleanup/abort semantics. |
| Demo transport | `DemoAIService`, `DemoAIGateway`, `DemoPostgres`, `DemoAgent` | Account-backed APIs are locally verifiable without pretending the remote service ran. |
| `.raw` escape hatch | `service.raw`, `handle.raw`, `session.raw` | New Cloudflare APIs remain reachable before wrappers catch up. |

## Naming policy

Use product vocabulary, but keep suffixes meaningful:

| Name shape | Use for | Examples |
|---|---|---|
| `*Service` | Native Worker binding facade or action boundary. | `QueueService`, `WorkflowService`, `AIService`, `PromptService` |
| `*Client` | REST/API-token client that calls an HTTP API. | `R2SqlClient`; future `ImagesClient` |
| Product noun | Official product facade when the product name is already the clearest name. | `AIGateway`, `R2DataCatalog`, `BrowserRendering` |
| `*Ref` | Passive handle to a named resource. | `R2ObjectRef`, `CounterRef`, `TableRef` |
| `*Session` | Active conversational or stateful interaction. | `AgentSession`, future `WebSocketSession` |
| `Demo*` | Deterministic local stand-in for a product or binding. | `DemoAIService`, `DemoVectorIndex`, `DemoPostgres` |
| `Fake*` | Tiny test harness object that mimics raw platform input, not a product. | `FakeQueueBatch`, `FakeQueueMessage` |

Prefer product-qualified nouns when a generic Cloudflare word would collide across products: `CatalogNamespace`, not `Namespace`.

## Type-system leverage

Xampler uses modern Python typing to make examples teachable and checkable:

- `dataclass(frozen=True)` for immutable request/result payloads.
- `Protocol` for swappable real/demo transports and Runnable-style chains.
- `TypeVar` and generic helpers in `xampler.streaming` for typed streams and batches.
- `Literal` for finite states and event kinds such as `"running"`, `"complete"`, `"token"`, `"tool_call"`.
- `Any` is kept at the JavaScript/Cloudflare boundary; business logic should convert to typed Python values quickly.
- `pyright` runs in strict mode for the shared `xampler/` package so reusable helpers do not silently drift.

The target is not to type every Cloudflare `JsProxy` directly. The target is to contain `Any` at the boundary, convert with `cfboundary`, and expose typed Python values from wrappers.

## Expanded primitive hero surfaces

| Primitive | Hero features surfaced in Xampler |
|---|---|
| Workers | Class-based `WorkerEntrypoint`; request parsing via Python stdlib; typed response helpers; JSON/text/binary responses; no legacy `on_fetch`. |
| R2 | Shared `xampler.r2` wrapper; object handles; text/JSON/bytes helpers; metadata and HTTP metadata; listing and async iteration; streaming reads; byte-for-byte JPEG fixture; multipart `async with`; `.raw`. |
| KV | Key handles; text/JSON helpers; exists/delete; list and async key iteration; platform aliases; missing-key behavior. |
| D1 | Statement handles; bound parameters; `one`, `all`, `one_as(Model)`; D1 null conversion; indexed query plan route; local setup automation. |
| FastAPI / ASGI | Normal `FastAPI()` routes; ASGI bridge; environment access through ASGI scope; local framework verification. |
| LangChain/package orchestration | `PromptInput`/`PromptOutput`; `PromptTemplate`; Runnable-style `PromptChain.invoke`; service boundary around package orchestration. |
| Workers Assets | Static assets do not wake Python; dynamic `/api/*` route does; verifier proves static/dynamic separation. |
| Durable Objects | Namespace wrapper; named-object handle; storage-backed state; typed ref methods; named-object isolation verification. |
| Cron Triggers | `ScheduledEventInfo`; `ScheduledRunResult`; job service object; local scheduled handler endpoint. |
| Workers AI | Typed text-generation request/result; service wrapper; deterministic demo service; real binding route retained. |
| Workflows | Workflow service; start/status shapes; instance handle; typed status result; durable-step vocabulary; demo status polling. |
| HTMLRewriter | Metadata dataclass; escaped OpenGraph injection; transformation wrapper; executable edge HTML response. |
| Binary responses | Dependency-free PNG bytes; content-type and PNG signature verification; teaches binary response correctness, not Cloudflare Images. |
| Service Bindings / RPC | Python RPC method; TypeScript service binding client; local provider verification; cross-worker vocabulary retained. |
| Outbound WebSockets | Durable Object owns outbound socket; alarm-managed reconnect; Pyodide proxy callbacks; deterministic status seam. |
| Durable Objects + WebSockets | Room Durable Object; WebSocket hibernation API; browser client; persisted message history; deterministic room send/history route. |
| Queues | Typed job dataclass; send options; batch sends; consumer `QueueMessage`; ack/retry/backoff; deterministic consumer harness. |
| Vectorize | Typed vectors; dimension validation; upsert; query/query-by-id; get/delete; typed matches/results; deterministic local search. |
| Browser Rendering | `ScreenshotRequest`; `ScreenshotResult`; REST screenshot/content/PDF/scrape client; deterministic renderer; real API route shape. |
| Email Workers | `IncomingEmail`; `EmailDecision`; inspect/forward/reject policy; HTTP policy fixture; deployed `email()` handler path. |
| AI Gateway | OpenAI-compatible chat messages; `ChatRequest`; `ChatChoice`; gateway transport; deterministic gateway transport. |
| R2 SQL | Query object; read-only guard; single-table safety; automatic `LIMIT`; `explain()` route; deterministic SQL client; seeded table remote query. |
| R2 Data Catalog | `CatalogNamespace`; `TableRef`; Iceberg REST client; namespaces/tables listing; temporary table lifecycle; deterministic fixture catalog. |
| Pages | Static `public/`; file-routed Function; `pages dev` verifier; explicit note that Python Pages Functions are not supported today. |
| HVSC AI/data app | Pipeline service composes R2 + D1 + Queues + AI/vector seams; shard ingestion; progress/status; browser run-all/search flow. |
| Hyperdrive | `HyperdriveConfig.from_binding`; typed Postgres query/result; production/demo client split; `/config`, `/query`, `/demo`. |
| Agents SDK | Typed messages; tool calls; run result; deterministic tool; Durable Object session routing; `AgentSession` raw wrapper shape. |
| Streaming composition | `ByteStream.iter_bytes/text/lines`; `JsonlReader.records`; `RecordStream`; `aiter_batches`; `StreamCheckpoint`; checkpointed D1 line pipeline; AI/agent/WebSocket event streams. |

## Design rule

Every primitive should expose:

1. **Friendly Python surface** — handles, dataclasses, normal verbs.
2. **Cloudflare vocabulary** — bindings, queues, workflows, vectors, namespaces, tables.
3. **Status/progress** — for setup-dependent or long-running work.
4. **Deterministic demo transport** — local verification for account-backed APIs.
5. **`.raw` escape hatch** — direct access to the platform object/client.
