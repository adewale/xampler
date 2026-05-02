# Example Status and Pythonic-ness

Last reviewed: 2026-05-01. Python anchor: Python 3.13.

This is the operating status board for the repository. An example is not considered excellent just because the code imports: it should run with `uv run pywrangler dev`, have a verification path, and teach the Cloudflare primitive through Python-native APIs.

## Status levels

- **Verified**: `scripts/verify_examples.py <name>` has been run successfully in this workspace.
- **Runnable**: has a real Worker project and should run locally, but needs resource setup or has not yet been smoke-tested here.
- **Needs work**: code shape exists, but it is not yet a convincing runnable example.

## Scores

Scores use [`docs/pythonic-rubric.md`](pythonic-rubric.md). They consider readability, Python metaphors, dataclasses/types, async correctness, testability, platform honesty, and the friendly/platform/escape-hatch layering.

| Example | Primitive | Status | Verified command | Pythonic score | Why |
|---|---|---|---|---:|---|
| `examples/start/hello-worker` | Workers request/response | Verified | `uv run python scripts/verify_examples.py examples/start/hello-worker` | 8.0 | Tiny, readable, and executable. Limited API surface. |
| `examples/storage-data/r2-object-storage` | R2 object storage | Verified | `uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage` | 9.25 | Strongest API: `bucket.object(key)`, `read_text`, `write_bytes`, typed metadata/options, `async for`, multipart `async with`, `.raw` escape hatch, real R2 local verification. |
| `examples/storage-data/kv-namespace` | Workers KV | Verified | `uv run python scripts/verify_examples.py examples/storage-data/kv-namespace` | 8.8 | Strong service/resource shape with `KVNamespace` and `KVKey`; verifier covers text, JSON, list, delete, and missing-key behavior. Needs expiration/cache metadata docs. |
| `examples/start/fastapi-worker` | FastAPI on Workers | Verified | `uv run python scripts/verify_examples.py examples/start/fastapi-worker` | 8.0 | Uses real ASGI bridge, keeps FastAPI routes ordinary, and verifies local routing. Needs `/env` and template/dependency route coverage. |
| `examples/storage-data/d1-database` | D1 | Verified | `uv run python scripts/verify_examples.py examples/storage-data/d1-database` | 8.7 | Verifier initializes local D1 with `db_init.sql`, starts the Worker, checks the seeded PEP 20 row, and verifies a parameter-bound query through `D1Statement.one_as`. Needs transactions/retries/index examples. |
| `examples/ai-agents/langchain-style-chain` | Python package / LangChain boundary | Verified | `uv run python scripts/verify_examples.py examples/ai-agents/langchain-style-chain` | 8.1 | Typed LCEL-style Runnable chain with prompt/model/service boundary and local verification. |
| `examples/start/static-assets` | Workers Assets | Verified | `uv run python scripts/verify_examples.py examples/start/static-assets` | 8.9 | Teaches the Pythonic/platform-correct approach: static assets bypass Python while `/api/status` wakes the Worker only for dynamic work. |
| `examples/state-events/durable-object-counter` | Durable Objects | Verified | `uv run python scripts/verify_examples.py examples/state-events/durable-object-counter` | 8.6 | Real named Durable Object, typed `CounterRef`, reset/increment/read verified across two isolated names. Good literate comments. Needs concurrent increment checks. |
| `examples/state-events/cron-trigger` | Cron triggers | Runnable | `uv run python scripts/verify_examples.py examples/state-events/cron-trigger` | 8.0 | Real scheduled handler and job object. Needs local scheduled endpoint verification. |
| `examples/state-events/queues-producer-consumer` | Queues | Verified producer | `uv run python scripts/verify_examples.py examples/state-events/queues-producer-consumer` | 8.5 | Real producer/consumer code with typed `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueBatchResult`, and ack/retry handling. Producer route is locally verified; consumer processing still needs a harness. |
| `examples/ai-agents/workers-ai-inference` | Workers AI | Runnable with runtime support | verifier listed | 8.25 | Typed request dataclass and `AIService`. Needs verified local/deployed AI run and typed response model. |
| `examples/state-events/workflows-pipeline` | Workflows | Runnable with runtime support | verifier listed | 7.75 | Real workflow entrypoint and `/start`/`/status`. Needs verified workflow run and `WorkflowInstance` handle. |
| `examples/network-edge/htmlrewriter-opengraph` | HTMLRewriter | Runnable | verifier listed | 7.75 | Has metadata model and executable response, but should use real `HTMLRewriter` boundary instead of prebuilt HTML. |
| `examples/streaming/binary-response` | Binary response | Verified | `uv run python scripts/verify_examples.py examples/streaming/binary-response` | 8.2 | Dependency-free deterministic PNG bytes with content-type and signature verification. |
| `examples/network-edge/service-bindings-rpc` | Service bindings / RPC | Verified provider | `uv run python scripts/verify_examples.py examples/network-edge/service-bindings-rpc/py` | 8.3 | Python RPC service plus TS client config; provider is locally verified. Needs full two-worker verifier. |
| `examples/network-edge/outbound-websocket-consumer` | Outbound WebSockets + Durable Objects | Verified | `uv run python scripts/verify_examples.py examples/network-edge/outbound-websocket-consumer` | 8.2 | Real outbound WebSocket consumer plus deterministic `/demo/status` verifier. |
| `examples/state-events/durable-object-chatroom` | Durable Objects + WebSockets | Runnable/browser-verifiable | verifier listed for page | 8.0 | Real chatroom page and DO WebSocket room. Needs automated WebSocket client verification. |

## Current verified set

The following have been run and passed in this workspace:

```bash
uv run python scripts/verify_examples.py examples/start/hello-worker
uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage
uv run python scripts/verify_examples.py examples/storage-data/kv-namespace
uv run python scripts/verify_examples.py examples/start/fastapi-worker
uv run python scripts/verify_examples.py examples/storage-data/d1-database
uv run python scripts/verify_examples.py examples/state-events/durable-object-counter
uv run python scripts/verify_examples.py examples/start/static-assets
uv run python scripts/verify_examples.py examples/state-events/queues-producer-consumer
uv run python scripts/verify_examples.py examples/streaming/binary-response
uv run python scripts/verify_examples.py examples/network-edge/htmlrewriter-opengraph
uv run python scripts/verify_examples.py examples/state-events/cron-trigger
uv run python scripts/verify_examples.py examples/ai-agents/langchain-style-chain
uv run python scripts/verify_examples.py examples/network-edge/service-bindings-rpc/py
uv run python scripts/verify_examples.py examples/network-edge/outbound-websocket-consumer
uv run python scripts/verify_examples.py examples/network-edge/browser-rendering-screenshot
uv run python scripts/verify_examples.py examples/network-edge/email-worker-router
uv run python scripts/verify_examples.py examples/ai-agents/ai-gateway-chat
uv run python scripts/verify_examples.py examples/storage-data/r2-data-catalog
uv run python scripts/verify_examples.py examples/storage-data/hyperdrive-postgres
uv run python scripts/verify_examples.py examples/ai-agents/agents-sdk-tools
uv run python scripts/verify_examples.py examples/streaming/gutenberg-stream-composition
```

## Pythonic themes that are working

1. **Service wrappers over bindings**: `R2Bucket`, `KVNamespace`, `D1Database`, `WorkflowService`.
2. **Resource handles**: `R2ObjectRef`, `KVKey`, Durable Object named stubs.
3. **Native values**: `str`, `bytes`, `dict`, `None`, dataclasses.
4. **Lifecycle protocols**: R2 multipart supports `async with`.
5. **Iteration protocols**: R2 has `iter_objects()`.
6. **Runtime honesty**: examples explain Pyodide proxies, JS streams, ASGI bridging, and static asset bypass.

## Priority iteration backlog

1. Raise level-3 examples to richer level-4 local harnesses.
2. Add KV TTL/expiration and metadata verification.
3. Add D1 transactions/retries/index examples now that setup automation exists.
4. Add queue consumer ack/retry verification beyond producer enqueue.
5. Replace `examples/network-edge/htmlrewriter-opengraph` simplified HTML with real HTMLRewriter usage.
6. Add deterministic WebSocket verification for the chatroom.
7. Add env-gated remote verification for account-backed products.
