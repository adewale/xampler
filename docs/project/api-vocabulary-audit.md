# API vocabulary audit

Last reviewed: 2026-05-01.

This audit checks whether importable `xampler/` modules follow the vocabulary in [`../api/vocabulary.md`](../api/vocabulary.md):

```text
Service → Ref → Request/Options → Result → Event/Handler → Stream/Page/Batch → Status → Policy → Demo → Raw
```

## Findings

| Area | Status | Notes |
|---|---|---|
| R2 | Consistent | `R2Bucket` is a service; `R2ObjectRef` is a ref; range/conditionals are options; list/object info are results; byte streams and multipart map to stream/batch lifecycle vocabulary. |
| KV | Consistent | `KVNamespace` follows Cloudflare product naming as the service; `KVKey` is a ref; list results model pages/cursors. |
| D1 | Consistent | `D1Database` is a service; `D1Statement` is an operation handle/ref-like object; query results remain Python rows or typed dataclasses. |
| Durable Objects | Consistent | `DurableObjectNamespace` is the service around a DO namespace binding; `DurableObjectRef` is the named-object ref. Product-specific refs such as counters stay example-local. |
| Queues | Fixed | `QueueTrackerNamespace`/`QueueTrackerRef` were removed from `xampler.queues` because they were Durable Object observability helpers, not Queue APIs. The shared queue surface is now `QueueService`, `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueConsumer`, `QueueBatchResult`, and `QueueEventRecorder`. The Durable Object tracker is renamed `QueueProcessingTracker*` and lives in the queue example. |
| Workflows | Consistent | `WorkflowService` starts and checks workflow runs; `WorkflowInstance` is the ref; `WorkflowStatus` is product-specific status. |
| Cron | Experimental | Moved to `xampler.experimental.cron` because it is currently event/result types plus `DemoScheduledJob`, not a full binding wrapper. |
| Service Bindings | Experimental | Moved to `xampler.experimental.service_bindings`; the helper is useful for the RPC example, but the final Service Bindings API shape should be proven by more real binding examples. |
| WebSockets | Experimental | Moved to `xampler.experimental.websockets` because the current surface is status/message/demo-session oriented; richer refs/sessions should wait for a real app shape. |
| Workers AI / AI Gateway / Vectorize / Agents | Consistent | Request/result/demo shapes are explicit. Capability Protocols avoid making `Demo*` classes subclasses of real services. |
| Browser Rendering / R2 SQL / R2 Data Catalog | Consistent | REST-backed surfaces use `RestClient` or clear product clients. Data Catalog namespaces/tables are official product resources, not generic Cloudflare namespaces. |
| Email / HTMLRewriter | Experimental | Moved to `xampler.experimental.email` and `xampler.experimental.htmlrewriter`; both are currently type/policy/fixture helpers before real binding wrappers. |
| Hyperdrive | Consistent | `HyperdrivePostgres` is a service-like query boundary over `HyperdriveConfig`; real remote Postgres execution remains future work. |
| Streaming / Status | Consistent | `StreamCheckpoint` was removed. Resumable work now uses `xampler.status.Checkpoint`; streaming owns streams/readers/events only. |

## Rules reinforced by this audit

1. Do not put helper Durable Objects inside a product module unless the product is Durable Objects.
2. If a helper is only for verifier observability, keep it example-local or make it a small Protocol capability.
3. Use product modules for reusable product vocabulary only.
4. Keep product-specific statuses where they describe real Cloudflare state; use `Progress`, `Checkpoint`, and `BatchResult` for shared long-running work.
5. Prefer example-local event/timeline dataclasses until multiple examples prove one shared shape.
6. Move type/demo-only product surfaces into `xampler.experimental` until there is a real binding or client wrapper worth making canonical.
