# API Surface Consistency Audit

Last reviewed: 2026-05-02.

This audit covers four known weaknesses: local-only wrappers, naming drift, deterministic demo transports, and inconsistent use of shared streaming helpers.

## Summary

| Area | Current state | Risk | Recommendation |
|---|---|---|---|
| Local wrappers | Most product wrappers still live beside their example. | Repeated patterns drift and are harder to type-check globally. | Extract only stable cross-example contracts first: `SupportsRaw`, response/status, demo transport, progress/checkpoint, batch result. |
| Naming uniformity | Broadly understandable but not fully systematic. | Users learn several names for the same concept. | Standardize suffixes: `*Service` for binding facades, `*Ref` for handles, `*Client` for REST clients, `Demo*` for deterministic stand-ins. |
| Demo transports | Valuable and honest, but shape varies by example. | Test realism can be mistaken for product realism; demo route names are not all uniform. | Keep `/demo` routes, add `DemoTransport` Protocol usage, and add env-gated remote verifiers. |
| Streaming helpers | `xampler.streaming` exists, but the Gutenberg example duplicates it locally and other examples do not import it. | The strongest composability API is not actually reused yet. | Make Gutenberg consume `xampler.streaming`, then adopt it in R2, HVSC, AI/Agents, WebSockets, and Queues. |

## 1. Wrappers still local to examples

Local wrappers are useful for teaching because readers see the whole product shape in one file. The downside is repetition: `raw` storage, dataclass outputs, `.raw` escape hatches, demo routes, and service naming reappear with small differences.

Representative local wrappers:

| Example | Local wrappers |
|---|---|
| `storage-data/r2-object-storage` | `R2Bucket`, `R2ObjectRef`, `R2Object`, `R2MultipartUpload` |
| `storage-data/kv-namespace` | `KVNamespace`, `KVKey` |
| `storage-data/d1-database` | `D1Database`, `D1Statement` |
| `state-events/queues-producer-consumer` | `QueueService`, `QueueConsumer`, `QueueMessage` |
| `state-events/workflows-pipeline` | `WorkflowService`, `WorkflowInstance` |
| `state-events/durable-object-counter` | `CounterNamespace`, `CounterRef` |
| `ai-agents/vectorize-search` | `VectorIndex`, `VectorQuery`, `VectorQueryResult` |
| `ai-agents/workers-ai-inference` | `AIService`, `TextGenerationRequest`, `TextGenerationResponse` |
| `ai-agents/agents-sdk-tools` | `AgentSession`, `AgentTool`, `AgentRunResult` |
| `full-apps/hvsc-ai-data-search` | `R2Artifacts`, `D1Database`, `QueueService`, `DemoVectorIndex` |

### Extraction priority

Do not move every product wrapper into `xampler/` at once. Start with the boring, repeated contracts:

1. `xampler.types.SupportsRaw` and key/id `NewType`s — started.
2. `xampler.demo.DemoTransport` plus route/result conventions.
3. `xampler.status.OperationState`, `Progress`, `BatchResult`, `Checkpoint`.
4. `xampler.response` JSON/error helpers.
5. `xampler.bindings.BindingService` / `ResourceRef` protocols only, not full product wrappers.

Product wrappers such as `R2Bucket`, `D1Database`, and `VectorIndex` should move only after at least three examples need the same API, or after pyright coverage is extended to those wrappers.

## 2. Naming uniformity

### Patterns that work

| Pattern | Meaning | Examples |
|---|---|---|
| `*Service` | Native binding facade or workflow/action boundary | `QueueService`, `WorkflowService`, `AIService`, `PromptService` |
| `*Client` | REST/API-token client, not a Worker binding | `R2SqlClient` |
| `*Ref` | Handle to a named remote resource | `R2ObjectRef`, `CounterRef` |
| `*Instance` | Handle to a long-running object/run | `WorkflowInstance` |
| `Demo*` | Deterministic local stand-in | `DemoAIService`, `DemoVectorIndex`, `DemoWorkflowService` |
| Dataclass nouns | Typed request/result values | `VectorQuery`, `QueueJob`, `ScreenshotResult` |

### Naming drift

| Drift | Example | Suggested convention |
|---|---|---|
| Binding facade sometimes named by product only | `BrowserRendering`, `AIGateway`, `R2DataCatalog` | Either allow product nouns for product clients, or rename consistently to `BrowserRenderingClient`, `AIGatewayClient`, `R2DataCatalogClient`. |
| Generic namespace names | R2 Data Catalog now uses `CatalogNamespace`. | Keep product-qualified names when a concept could appear in multiple products. |
| Demo/fake words both used | `DemoVectorIndex`, `FakeQueueBatch` | Use `Demo*` for deterministic product stand-ins; reserve `Fake*` for tiny test harness objects that mimic raw platform messages. |
| State/status names vary | `StreamCheckpoint`, `WorkflowStatus`, `QueueBatchResult`, HVSC ingest state dicts | Create shared `OperationState`, `Checkpoint`, `BatchResult` vocabulary. |
| Resource handle suffix varies | `KVKey`, `R2ObjectRef`, `TableRef`, `AgentSession` | Prefer `*Ref` for passive handles and `*Session` only for active conversational/stateful sessions. |

## 3. Deterministic demo transports

Demo transports are a strength when labeled honestly: they let examples pass locally while keeping real Cloudflare API vocabulary visible. They become a weakness when each product invents a different seam.

Current demo/stand-in examples:

| Example | Stand-in | Why it exists | Next realism step |
|---|---|---|---|
| Workers AI | `DemoAIService` | AI binding is remote/account-backed. | Env-gated remote AI verifier. |
| AI Gateway | `DemoAIGateway` | Needs account/gateway/token. | Remote gateway verifier with request id/header checks. |
| Vectorize | `DemoVectorIndex` | Needs account index. | Remote index create/upsert/query verifier. |
| Workflows | `DemoWorkflowService` | Local workflow runtime limits. | Deployed workflow start/status verifier. |
| Queues | `FakeQueueBatch`, `FakeQueueMessage` | Local producer is easy; delivery/DLQ is harder to force deterministically. | Remote delivery and DLQ verifier. |
| Browser Rendering | `DemoBrowserRendering` | Needs browser binding/API entitlement. | Remote screenshot verifier. |
| R2 SQL / Data Catalog | `DemoR2SqlClient`, `DemoR2DataCatalog` | Account-backed APIs. | Remote query/catalog verifier. |
| Hyperdrive | `DemoPostgres` | Needs Postgres + Hyperdrive config. | Remote Hyperdrive query verifier. |
| Agents | `DemoAgent` | Agents SDK parity is still evolving. | Direct Cloudflare Agents SDK interop verifier. |

### Recommendation

Adopt a uniform interface:

```python
RequestT = TypeVar("RequestT")
ResultT = TypeVar("ResultT")

class DemoTransport(Protocol[RequestT, ResultT]):
    async def run(self, request: RequestT) -> ResultT: ...
```

And a uniform route convention:

- `/demo` for deterministic local product shape.
- `/` or product-specific route for real binding/API path.
- `XAMPLER_REMOTE=1` or explicit verifier profile for account-backed remote checks.

## 4. Streaming helper reuse

`xampler.streaming` contains:

- `ByteStream`
- `RecordStream`
- `JsonlReader`
- `aiter_batches`
- `async_enumerate`
- `StreamCheckpoint`
- `AgentEvent`

The Gutenberg example now imports these shared helpers, so the original duplication is fixed there. Follow-up audit: [`api-surface-follow-up-audit.md`](api-surface-follow-up-audit.md).

### Current streaming usage

| Example | Current state | Recommendation |
|---|---|---|
| `streaming/gutenberg-stream-composition` | Imports `ByteStream`, `JsonlReader`, `StreamCheckpoint`, `AgentEvent`, `aiter_batches`, and `async_enumerate` from `xampler.streaming`. Still keeps JS R2 `ReadableStream` conversion local because it is Workers-specific. | Add `readable_stream_chunks` to shared module if pyright-safe. |
| `storage-data/r2-object-storage` | Has R2-specific stream helpers in `r2_pythonic.py`. | Return or adapt to shared `ByteStream` where useful; keep R2-specific body conversion local or in a boundary helper. |
| `full-apps/hvsc-ai-data-search` | Uses shard-oriented ingestion and D1 progress, not shared stream types. | Model catalog shard reads as `ByteStream -> JsonlReader -> aiter_batches`. |
| `ai-agents/*` | AI/agent streams are demonstrated as local async iterators in Gutenberg only. | Reuse `AgentEvent` and `stream_text()` vocabulary in AI/Agents examples. |
| `durable-object-chatroom` / WebSockets | Real WebSocket broadcast verifier exists, but not exposed as `async for` session API. | Add `WebSocketSession.__aiter__()` wrapper shape when extracting shared streaming/event helpers. |

## Proposed cleanup order

1. Add `xampler.response` and `xampler.status`; replace the most duplicated local status/result helpers.
2. Introduce shared Protocols only: `BindingService`, `ResourceRef`, `DemoTransport`, `RemoteVerifier`.
3. Normalize naming in new examples immediately; avoid mass-renaming old examples unless touching them anyway.
4. Add remote verifier profiles so `Demo*` remains clearly separate from real product verification.
5. Only then extract stable product wrappers, starting with R2/D1/KV because they have the best local realism.
