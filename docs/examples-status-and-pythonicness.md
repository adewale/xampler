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
| `workers-01-hello` | Workers request/response | Verified | `uv run python scripts/verify_examples.py workers-01-hello` | 8.0 | Tiny, readable, and executable. Limited API surface. |
| `r2-01` | R2 object storage | Verified | `uv run python scripts/verify_examples.py r2-01` | 9.25 | Strongest API: `bucket.object(key)`, `read_text`, `write_bytes`, typed metadata/options, `async for`, multipart `async with`, `.raw` escape hatch, real R2 local verification. |
| `kv-02-binding` | Workers KV | Verified | `uv run python scripts/verify_examples.py kv-02-binding` | 8.8 | Strong service/resource shape with `KVNamespace` and `KVKey`; verifier covers text, JSON, list, delete, and missing-key behavior. Needs expiration/cache metadata docs. |
| `fastapi-03-framework` | FastAPI on Workers | Verified | `uv run python scripts/verify_examples.py fastapi-03-framework` | 8.0 | Uses real ASGI bridge, keeps FastAPI routes ordinary, and verifies local routing. Needs `/env` and template/dependency route coverage. |
| `d1-04-query` | D1 | Verified | `uv run python scripts/verify_examples.py d1-04-query` | 8.7 | Verifier initializes local D1 with `db_init.sql`, starts the Worker, checks the seeded PEP 20 row, and verifies a parameter-bound query through `D1Statement.one_as`. Needs transactions/retries/index examples. |
| `ai-05-langchain` | Python package / LangChain boundary | Needs work | none yet | 6.75 | Service boundary shape is useful, but it does not yet exercise a real LangChain chain in Workers. |
| `assets-06-static-assets` | Workers Assets | Verified | `uv run python scripts/verify_examples.py assets-06-static-assets` | 8.9 | Teaches the Pythonic/platform-correct approach: static assets bypass Python while `/api/status` wakes the Worker only for dynamic work. |
| `durable-objects-07-counter` | Durable Objects | Verified | `uv run python scripts/verify_examples.py durable-objects-07-counter` | 8.6 | Real named Durable Object, typed `CounterRef`, reset/increment/read verified across two isolated names. Good literate comments. Needs concurrent increment checks. |
| `scheduled-08-cron` | Cron triggers | Runnable | `uv run python scripts/verify_examples.py scheduled-08-cron` | 8.0 | Real scheduled handler and job object. Needs local scheduled endpoint verification. |
| `queues-16-producer-consumer` | Queues | Verified producer | `uv run python scripts/verify_examples.py queues-16-producer-consumer` | 8.5 | Real producer/consumer code with typed `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueBatchResult`, and ack/retry handling. Producer route is locally verified; consumer processing still needs a harness. |
| `workers-ai-09-inference` | Workers AI | Runnable with runtime support | verifier listed | 8.25 | Typed request dataclass and `AIService`. Needs verified local/deployed AI run and typed response model. |
| `workflows-10-pipeline` | Workflows | Runnable with runtime support | verifier listed | 7.75 | Real workflow entrypoint and `/start`/`/status`. Needs verified workflow run and `WorkflowInstance` handle. |
| `htmlrewriter-11-opengraph` | HTMLRewriter | Runnable | verifier listed | 7.75 | Has metadata model and executable response, but should use real `HTMLRewriter` boundary instead of prebuilt HTML. |
| `images-12-generation` | Pillow / binary response | Runnable | verifier listed | 8.0 | Real Pillow-generated PNG. Needs typed query parameters and cache/R2 integration. |
| `service-bindings-13-rpc` | Service bindings / RPC | Runnable with two processes | manual two-worker run | 8.0 | Python RPC service plus TS client config. Needs one-command verifier for both services. |
| `websockets-14-stream-consumer` | Outbound WebSockets + Durable Objects | Runnable with network | verifier listed | 7.75 | Real outbound WebSocket consumer, alarm reconnect, Pyodide proxy explanation. Needs deterministic local test. |
| `durable-objects-15-chatroom` | Durable Objects + WebSockets | Runnable/browser-verifiable | verifier listed for page | 8.0 | Real chatroom page and DO WebSocket room. Needs automated WebSocket client verification. |

## Current verified set

The following have been run and passed in this workspace:

```bash
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
uv run python scripts/verify_examples.py kv-02-binding
uv run python scripts/verify_examples.py fastapi-03-framework
uv run python scripts/verify_examples.py d1-04-query
uv run python scripts/verify_examples.py durable-objects-07-counter
uv run python scripts/verify_examples.py assets-06-static-assets
uv run python scripts/verify_examples.py queues-16-producer-consumer
uv run python scripts/verify_examples.py images-12-generation
uv run python scripts/verify_examples.py htmlrewriter-11-opengraph
uv run python scripts/verify_examples.py scheduled-08-cron
```

## Pythonic themes that are working

1. **Service wrappers over bindings**: `R2Bucket`, `KVNamespace`, `D1Database`, `WorkflowService`.
2. **Resource handles**: `R2ObjectRef`, `KVKey`, Durable Object named stubs.
3. **Native values**: `str`, `bytes`, `dict`, `None`, dataclasses.
4. **Lifecycle protocols**: R2 multipart supports `async with`.
5. **Iteration protocols**: R2 has `iter_objects()`.
6. **Runtime honesty**: examples explain Pyodide proxies, JS streams, ASGI bridging, and static asset bypass.

## Priority iteration backlog

1. Add automated smoke verification for every Runnable example.
2. Add KV TTL/expiration and metadata verification.
3. Add D1 transactions/retries/index examples now that setup automation exists.
4. Add queue consumer ack/retry verification beyond producer enqueue.
5. Replace `htmlrewriter-11-opengraph` simplified HTML with real HTMLRewriter usage.
6. Add deterministic WebSocket verification for the chatroom.
7. Turn `ai-05-langchain` into a real working LangChain-compatible example or drop it from the verified set.
