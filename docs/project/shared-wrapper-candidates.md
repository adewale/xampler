# Shared Wrapper Package Candidates

Last reviewed: 2026-05-02.

Xampler should lift only stable, boring, repeated concepts into `xampler/`. Product hero logic should stay in examples until it has proved itself across multiple primitives.

## Already shared

| Module | Contents |
|---|---|
| `xampler.streaming` | `ByteStream`, `RecordStream`, `JsonlReader`, `aiter_batches`, `StreamCheckpoint`, `AgentEvent`. |
| `xampler.types` | `JsonObject`, `R2Key`, `QueueName`, `WorkflowId`, `VectorId`, `AgentId`, `SupportsRaw`, `DemoTransport`, `RemoteVerifier`. |
| `xampler.status` | `OperationState`, `Progress`, `Checkpoint`, generic `BatchResult`. |
| `xampler.response` | `jsonable()` and `error_payload()` helpers for dataclass/native response payloads. |
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

## Best candidates to extract next

| Candidate module | Repeated concepts | Why now |
|---|---|---|
| `xampler.testing` | verifier process helpers, remote-skip conventions, env guards | `scripts/verify_examples.py` is growing custom cases. |
| `xampler.bindings` | additional base protocols only if `xampler.cloudflare` proves insufficient | Common wrapper shape without hiding product vocabulary. |
| `xampler.durable_objects` | object namespace/ref patterns | DO examples still have product-specific HTML/WebSocket state mixed into route code. |
| `xampler.workflows` | workflow start/status and instance refs | Workflow wrapper is stable enough to consider next. |
| `xampler.demo` | `DemoTransport` conventions and route naming | Account-backed products use the same real/demo split. |

## Do not extract yet

| Keep local | Reason |
|---|---|
| Durable Object, Workflow, Hyperdrive, AI Gateway, Agents, Email, HTMLRewriter product wrappers | They still mix route/demo-specific behavior with product API shape or need more remote realism. |
| Additional Cloudflare REST clients | Product-specific auth/metadata varies too much until examples prove stable shapes. |
| Demo product logic | Useful to read beside the example it supports. |

## Extraction rule

Extract when all are true:

1. the pattern appears in at least three examples;
2. the shared abstraction is smaller than the duplicated code;
3. it does not hide Cloudflare product vocabulary;
4. it can be covered by strict `pyright` and unit tests.
