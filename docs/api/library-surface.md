# Xampler library surface

Xampler is a Python library with examples that prove the APIs run in Python Workers.

## Import map

| Module | Status | Primary imports |
|---|---|---|
| `xampler.r2` | Stable | `R2Bucket`, `R2ObjectRef`, `R2HttpMetadata`, `R2Range`, `R2Conditional` |
| `xampler.d1` | Stable | `D1Database`, `D1Statement` |
| `xampler.kv` | Stable | `KVNamespace`, `KVKey`, `KVListResult` |
| `xampler.streaming` | Stable | `ByteStream`, `JsonlReader`, `aiter_batches`, `AgentEvent` |
| `xampler.response` | Stable | `jsonable`, `error_payload` |
| `xampler.status` | Stable | `Progress`, `Checkpoint`, `BatchResult` |
| `xampler.cloudflare` | Stable base | `CloudflareService`, `ResourceRef`, `RestClient` |
| `xampler.queues` | Beta | `QueueService`, `QueueJob`, `QueueConsumer`, `QueueEventRecorder`, `QueueBatchResult` |
| `xampler.vectorize` | Beta | `VectorIndex`, `Vector`, `VectorQuery`, `DemoVectorIndex` |
| `xampler.ai` | Beta | `AIService`, `TextGenerationRequest`, `DemoAIService` |
| `xampler.browser_rendering` | Experimental | `BrowserRendering`, `ScreenshotRequest` |
| `xampler.r2_sql` | Experimental | `R2SqlClient`, `R2SqlQuery`, `DemoR2SqlClient` |
| `xampler.r2_data_catalog` | Experimental | `R2DataCatalog`, `CatalogNamespace`, `TableRef` |
| `xampler.durable_objects` | Beta | `DurableObjectNamespace`, `DurableObjectRef` |
| `xampler.workflows` | Beta | `WorkflowService`, `WorkflowInstance`, `WorkflowStatus`, `DemoWorkflowService` |
| `xampler.cron` | Beta | `ScheduledEventInfo`, `ScheduledRunResult`, `DemoScheduledJob` |
| `xampler.service_bindings` | Beta | `ServiceBinding`, `RpcCall`, `RpcResult`, `DemoServiceBinding` |
| `xampler.websockets` | Beta | `WebSocketStatus`, `DemoWebSocketSession` |
| `xampler.agents` | Experimental | `AgentSession`, `AgentMessage`, `ToolCall`, `AgentRunResult`, `DemoAgent` |
| `xampler.ai_gateway` | Experimental | `AIGateway`, `ChatRequest`, `ChatMessage`, `ChatResponse`, `DemoAIGateway` |
| `xampler.email` | Experimental | `IncomingEmail`, `EmailDecision`, `EmailRouter` |
| `xampler.htmlrewriter` | Experimental | `OpenGraphPage`, `OpenGraphRewriter` |
| `xampler.hyperdrive` | Experimental | `HyperdriveConfig`, `PostgresQuery`, `PostgresResult`, `HyperdrivePostgres`, `DemoPostgres` |

## Base vocabulary: service, ref, REST client

`xampler.cloudflare` has three tiny base classes. They are deliberately more semantic than functional: they document the role a wrapper plays in the Cloudflare boundary.

| Base | Meaning | Use for | Examples |
|---|---|---|---|
| `CloudflareService[T]` | Active wrapper around a Worker binding or runtime facade. | Code that calls binding methods and owns JS/Python boundary conversion. | `R2Bucket`, `D1Database`, `KVNamespace`, `QueueService`, `VectorIndex`, `AIService`, `WorkflowService` |
| `ResourceRef[T]` | Passive handle to one named resource reached through a service/namespace. | Cheap, passable references with domain verbs. | `KVKey`, `DurableObjectRef`, `WorkflowInstance` |
| `RestClient[T]` | Token/HTTP-backed client for Cloudflare APIs without a Python-usable Worker binding path. | Products that need account IDs, tokens, secrets, base URLs, or deployed REST verification. | `BrowserRendering`, `R2SqlClient`, `R2DataCatalog`, `AIGateway` |

The split is intentionally visible because it teaches where code runs and what credentials it needs:

- Use a **service** when Worker code has a binding such as `env.BUCKET`, `env.DB`, or `env.JOBS`.
- Use a **ref** when user code needs a stable handle to a named thing such as an R2 key, KV key, Durable Object name, or Workflow instance.
- Use a **REST client** when Worker code calls an HTTP API with explicit credentials/secrets instead of using a binding.

These bases should stay tiny. Product behavior belongs in product modules; route/UI/demo glue belongs in examples; `.raw` remains the escape hatch for platform features not yet wrapped.

## Stability meanings

- **Stable**: intended for users to import; covered by strict `pyright`, unit tests, and executable examples.
- **Beta**: intended for users to try; API may still change as remote verification deepens.
- **Experimental**: product/auth behavior is still evolving or token-backed verification is not regular yet.

## Design contract

The full vocabulary is documented in [`vocabulary.md`](vocabulary.md):

```text
Service → Ref → Request/Options → Result → Event/Handler → Stream/Page/Batch → Status → Policy → Demo → Raw
```

All product modules should preserve these rules:

1. Keep Cloudflare product vocabulary visible.
2. Wrap active bindings or clients in service/client classes.
3. Use dataclasses for request/result/options shapes.
4. Use `async for` for streams and pagination where applicable.
5. Keep `.raw` available for platform escape hatches.
6. Keep demo transports explicit as `Demo*`, never hidden as if real products ran locally.

## What stays in examples

Route handlers, HTML, verifier-only endpoints, fixtures, UI state, and app-specific pipeline logic stay in `examples/`. Library modules own reusable product API shape.
