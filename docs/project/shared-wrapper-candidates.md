# Shared Wrapper Package Candidates

Last reviewed: 2026-05-02.

Xampler is now a library-first project with executable examples. Stable reusable product APIs should live in `xampler/`; examples should keep route handlers, UI, fixtures, verifier endpoints, and app-specific orchestration.

## Already shared

| Module | Contents |
|---|---|
| `xampler.streaming` | `ByteStream`, `RecordStream`, `JsonlReader`, `aiter_batches`, `StreamCheckpoint`, `AgentEvent`. |
| `xampler.types` | `JsonObject`, `R2Key`, `QueueName`, `WorkflowId`, `VectorId`, `AgentId`, `SupportsRaw`, `DemoTransport`, `RemoteVerifier`. |
| `xampler.status` | `OperationState`, `Progress`, `Checkpoint`, generic `BatchResult`. |
| `xampler.response` | `jsonable()`, response constructors, and `error_payload()` helpers for dataclass/native response payloads. |
| `xampler.cloudflare` | `CloudflareService`, `ResourceRef`, `RestClient` base vocabulary. |
| `xampler.r2` | `R2Bucket`, `R2ObjectRef`, metadata/options dataclasses, listing, streaming, ranges, conditionals, and multipart upload. |
| `xampler.d1` | `D1Database`, `D1Statement`, parameter binding, row helpers, batch/execute helpers. |
| `xampler.kv` | `KVNamespace`, `KVKey`, text/JSON helpers, list/iteration helpers. |
| `xampler.queues` | `QueueService`, `QueueJob`, `QueueConsumer`, `QueueTrackerRef`, ack/retry result types. |
| `xampler.vectorize` | `VectorIndex`, vector/query/result dataclasses, demo vector index. |
| `xampler.ai` | `AIService`, text-generation request/result types, demo AI service. |
| `xampler.browser_rendering` | Browser Rendering REST client and screenshot request/result types. |
| `xampler.r2_sql` | R2 SQL REST client, guarded query type, result/demo client. |
| `xampler.r2_data_catalog` | Iceberg/R2 Data Catalog REST client, namespace/table types, demo catalog. |
| `xampler.durable_objects` | Durable Object namespace/ref patterns. |
| `xampler.workflows` | Workflow start/status and instance refs. |
| `xampler.cron` | Scheduled event/result shapes and demo scheduled job. |
| `xampler.service_bindings` | RPC-style service binding wrapper and demo binding. |
| `xampler.websockets` | WebSocket status/result vocabulary and demo session. |
| `xampler.agents` | Agent messages, tool calls, run results, and demo agent. |
| `xampler.ai_gateway` | AI Gateway chat request/response client and demo gateway. |

## Best candidates to extract next

| Candidate module | Repeated concepts | Why now |
|---|---|---|
| `xampler.testing` | verifier process helpers, remote-skip conventions, env guards | `scripts/verify_examples.py` is growing custom cases. |
| `xampler.bindings` | additional base protocols only if `xampler.cloudflare` proves insufficient | Common wrapper shape without hiding product vocabulary. |
| `xampler.email` | incoming email, decisions, router shape | Email example has a clear policy/router pattern but needs another fixture-heavy example. |
| `xampler.htmlrewriter` | metadata extraction and rewrite callbacks | HTMLRewriter needs another local fixture before the callback abstraction is stable. |
| `xampler.hyperdrive` | config/query/result shapes | Needs real Postgres/Hyperdrive verification before stabilizing. |
| `xampler.demo` | `DemoTransport` conventions and route naming | Account-backed products use the same real/demo split. |

## Keep example-local for now

| Keep local | Reason |
|---|---|
| Email, HTMLRewriter, and Hyperdrive product wrappers | They still mix route/demo-specific behavior with product API shape or need more remote realism. |
| Additional Cloudflare REST clients | Product-specific auth/metadata varies too much until examples prove stable shapes. |
| Demo product logic | Useful to read beside the example it supports. |

## Extraction rule

Extract when all are true:

1. the wrapper is reusable outside one route/UI demo;
2. the shared abstraction is smaller and clearer than the duplicated code;
3. it does not hide Cloudflare product vocabulary;
4. it can be covered by strict `pyright`, unit tests, and at least one executable example.
