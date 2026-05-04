# Xampler API vocabulary

Xampler uses one vocabulary across Cloudflare Developer Platform primitives:

```text
Service → Ref → Request/Options → Result → Event/Handler → Stream/Page/Batch → Status → Policy → Demo → Raw
```

This is the API surface hierarchy. Product modules should use these shapes before inventing new abstraction names.

## Vocabulary elements

| Element | Python shape | Meaning | Current examples |
|---|---|---|---|
| Service | `R2Bucket`, `D1Database`, `QueueService` | Active object that does work through a Worker binding, runtime facade, or product client. | R2, D1, KV, Queues, Vectorize, Workers AI, Workflows |
| Ref | `R2ObjectRef`, `KVKey`, `WorkflowInstance` | Cheap handle to one named resource reached through a service or namespace. | R2 object, KV key, Durable Object name, Workflow instance |
| Request | `VectorQuery`, `ChatRequest`, `PostgresQuery` | Structured operation input. | prompts, SQL, vector search, browser screenshot |
| Options | `R2Range`, `QueueSendOptions`, future `CacheOptions` | Optional product knobs. | R2 range/conditionals, queue delay, cache TTL, image transforms |
| Result | `ChatResponse`, `VectorQueryResult`, `PostgresResult` | Structured operation output. | AI text, vector matches, SQL rows, image metadata |
| Event | `ScheduledEventInfo`, `QueueMessage`, `IncomingEmail`, `AgentEvent` | Runtime-delivered or stream-delivered input. | cron, queues, email, WebSockets, logs, agents |
| Handler | `ScheduledJob`, `QueueConsumer`, `EmailRouter` | User code that processes events. | cron jobs, queue consumers, email routing, Durable Object methods |
| Stream | `ByteStream`, `RecordStream`, async iterators | Data arrives over time. | R2 bytes, AI tokens, WebSocket messages, logs, media |
| Page | product list results/cursors | Paginated listing. | KV list, R2 list, catalog tables, Images list |
| Batch | `BatchResult`, `QueueBatchResult`, batched D1 statements | Grouped work or grouped result. | queues, imports, D1 writes, Analytics Engine writes |
| Status | `Progress`, `Checkpoint`, `WorkflowStatus` | Long-running or resumable state. | workflows, uploads, ingestion jobs, stream processing |
| Policy | `EmailDecision`, future `AccessDecision` | Allow/reject/route/transform decision. | email, cache/auth/rate-limit examples, Turnstile verification |
| Demo | `DemoAIService`, `DemoVectorIndex` | Deterministic local substitute for account-backed or hard-to-run behavior. | AI, Vectorize, Browser Rendering, R2 SQL, Hyperdrive |
| Raw | `.raw` | Escape hatch to the underlying Cloudflare/runtime object. | binding/client wrappers |

## How the vocabulary covers Cloudflare products

| Cloudflare primitive/product | Service | Ref | Request/Options | Result/Status | Event/Handler | Stream/Page/Batch |
|---|---|---|---|---|---|---|
| Workers | Worker app/service boundary | route/path ref optional | HTTP request/options | `Response` helpers | `fetch` handler | request/response streams |
| Workers Builds | build/deploy service | project/build ref | build/deploy options | build/deploy status | deploy hook handler | build logs/events |
| Workers Assets | asset service/config | asset path | cache/header options | asset response | fallback handler | static file streams |
| Pages Functions | function service | route/file ref | request | response | function handler | asset/file streams |
| Service Bindings | `ServiceBinding` | bound service ref optional | `RpcCall` | `RpcResult` | RPC method handler | request/response |
| R2 | `R2Bucket` | `R2ObjectRef` | range, metadata, conditionals | object info/write result | notification handler later | byte stream, multipart, list pages |
| KV | `KVNamespace` | `KVKey` | TTL/cache/list options | value/list result | — | cursor pages |
| D1 | `D1Database` | `D1Statement` | SQL/params | rows/result metadata | — | batch SQL |
| Durable Objects | namespace/service | object/room ref | request/path/options | object state/status | `fetch`, alarm, WebSocket handlers | WebSocket/event streams |
| Queues | `QueueService` | queue/tracker ref | `QueueJob`, delay/retry options | `QueueBatchResult` | `QueueConsumer` | message batches, DLQ |
| Workflows | `WorkflowService` | workflow instance | start/status request | `WorkflowStatus`, `Progress`, `Checkpoint` | step handler | durable checkpoints |
| Cron Triggers | scheduled job service | — | `ScheduledEventInfo` | `ScheduledRunResult` | scheduled handler | — |
| Tail Workers / logs | tail/log service | tail session ref | filter options | log status/result | tail event handler | event stream/batches |
| Workers AI | `AIService` | model ref optional | text/image/embedding requests | AI results | — | token stream later |
| AI Gateway | `AIGateway` | gateway/model ref optional | `ChatRequest` | `ChatResponse`, provider metadata | — | streaming chat later |
| AutoRAG / managed retrieval | future retrieval service | index/corpus ref | search/query request | answer/citation result | — | result pages/streams |
| Vectorize | `VectorIndex` | vector id ref optional | `VectorQuery`, upsert request | matches/result | — | batch upsert, pages |
| Agents | `AgentSession` | agent/session ref | message/tool request | `AgentRunResult` | tool handler | message/tool-call stream |
| Browser Rendering | `BrowserRendering` | browser/page/session ref later | screenshot/PDF/content options | screenshot/PDF/content result | — | binary streams |
| R2 SQL | `R2SqlClient` | table ref optional | `R2SqlQuery` | SQL result/status | — | row batches |
| R2 Data Catalog | `R2DataCatalog` | namespace/table ref | schema/table lifecycle request | schema/table result | — | table pages |
| Hyperdrive | `HyperdrivePostgres` | connection/db ref optional | `PostgresQuery` | `PostgresResult` | — | row batches |
| Workers Analytics Engine | future `AnalyticsService` | dataset ref | write/query request | query result | ingestion handler | batch writes, result rows |
| Pipelines | future pipeline service | pipeline/job ref | ingest/route options | pipeline/job status | source/sink handler | event batches |
| Images | future `ImagesClient` | image/variant ref | upload/transform options | image metadata/result | webhook later | binary streams, list pages |
| Stream | future `StreamClient` | video/live input ref | upload/playback options | processing/playback status | webhook handler | media streams |
| Calls / Realtime | future realtime service | room/session/participant ref | token/session request | session status | WebRTC/WebSocket handlers | media/event streams |
| Pub/Sub-style messaging | future pubsub service | topic/subscription ref | publish/subscribe options | delivery status | message handler | message streams/batches |
| Email Workers | `EmailRouter` | message ref optional | `IncomingEmail` | `EmailDecision` | email handler | MIME stream later |
| HTMLRewriter | rewriter service | selector ref optional | selector/transform options | transformed HTML/metadata | element handler | HTML stream |
| Cache API | future `CacheService` | cache key ref | cache match/put options | hit/miss result | fetch middleware | response streams |
| Turnstile | future `TurnstileVerifier` | token ref optional | verify request | verification result/decision | form/API handler | — |
| Workers for Platforms / Dispatch | dispatch service | namespace/script/tenant ref | dispatch/deploy request | deployment/result/status | tenant handler | logs/events |
| Containers | future container service | container/session/process ref | start/exec request | lifecycle/output status | lifecycle handler | stdout/stderr streams |
| Secrets / Vars / Config | config service optional | secret/var name ref | create/update options | config status | — | pages |
| Observability / Logpush APIs | observability client | dataset/job ref | query/filter request | logs/metrics result | log handler | event streams/pages |

## Status vocabulary

Use one shared status vocabulary:

```python
from xampler.status import BatchResult, Checkpoint, Progress
```

- `Progress` means known-size work is underway.
- `Checkpoint` means work can resume from an offset/count.
- `BatchResult` means grouped work produced a count and often a checkpoint.

Product-specific statuses are still allowed where product vocabulary matters: `WorkflowStatus`, `WebSocketStatus`, and `QueueBatchResult` are examples. Timeline-style responses should be plain ordered **events** in an example until multiple examples prove the need for a shared type.

## Design rule

```text
Services do work.
Refs name things.
Requests/options describe inputs.
Results describe outputs.
Events arrive from Cloudflare or streams.
Handlers process events.
Streams/pages/batches move many things.
Status describes long-running work.
Policy returns decisions.
Demo proves local behavior.
.raw exposes the platform.
```
