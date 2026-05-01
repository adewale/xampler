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
| `workers-01-hello` | Workers request/response | Verified | `uv run python scripts/verify_examples.py workers-01-hello` | 3.2 | Tiny, readable, and executable. Limited API surface. |
| `r2-01` | R2 object storage | Verified | `uv run python scripts/verify_examples.py r2-01` | 3.7 | Strongest API: `bucket.object(key)`, `read_text`, `write_bytes`, typed metadata/options, `async for`, multipart `async with`, `.raw` escape hatch, real R2 local verification. |
| `kv-02-binding` | Workers KV | Verified | `uv run python scripts/verify_examples.py kv-02-binding` | 3.4 | Good service/resource shape with `KVNamespace` and `KVKey`; text/JSON helpers and local KV verification. Needs expiration/cache metadata docs. |
| `fastapi-03-framework` | FastAPI on Workers | Runnable | `uv run python scripts/verify_examples.py fastapi-03-framework` | 3.2 | Uses real ASGI bridge and keeps FastAPI routes ordinary. Needs smoke verification after dependency install. |
| `d1-04-query` | D1 | Runnable with setup | `npx wrangler d1 execute xampler-d1 --local --file db_init.sql` then verifier | 3.3 | Real D1 query wrapper and typed row. Needs automatic setup in verifier and richer statement/transaction helpers. |
| `ai-05-langchain` | Python package / LangChain boundary | Needs work | none yet | 2.7 | Service boundary shape is useful, but it does not yet exercise a real LangChain chain in Workers. |
| `assets-06-static-assets` | Workers Assets | Runnable | `uv run python scripts/verify_examples.py assets-06-static-assets` | 3.5 | Teaches the Pythonic/platform-correct approach: static assets should bypass Python. Needs smoke verification. |
| `durable-objects-07-counter` | Durable Objects | Verified | `uv run python scripts/verify_examples.py durable-objects-07-counter` | 3.3 | Real named Durable Object, reset/increment/read verified. Good literate comments. Could add a richer typed stub wrapper. |
| `scheduled-08-cron` | Cron triggers | Runnable | `uv run python scripts/verify_examples.py scheduled-08-cron` | 3.2 | Real scheduled handler and job object. Needs local scheduled endpoint verification. |
| `workers-ai-09-inference` | Workers AI | Runnable with runtime support | verifier listed | 3.3 | Typed request dataclass and `AIService`. Needs verified local/deployed AI run and typed response model. |
| `workflows-10-pipeline` | Workflows | Runnable with runtime support | verifier listed | 3.1 | Real workflow entrypoint and `/start`/`/status`. Needs verified workflow run and `WorkflowInstance` handle. |
| `htmlrewriter-11-opengraph` | HTMLRewriter | Runnable | verifier listed | 3.1 | Has metadata model and executable response, but should use real `HTMLRewriter` boundary instead of prebuilt HTML. |
| `images-12-generation` | Pillow / binary response | Runnable | verifier listed | 3.2 | Real Pillow-generated PNG. Needs typed query parameters and cache/R2 integration. |
| `service-bindings-13-rpc` | Service bindings / RPC | Runnable with two processes | manual two-worker run | 3.2 | Python RPC service plus TS client config. Needs one-command verifier for both services. |
| `websockets-14-stream-consumer` | Outbound WebSockets + Durable Objects | Runnable with network | verifier listed | 3.1 | Real outbound WebSocket consumer, alarm reconnect, Pyodide proxy explanation. Needs deterministic local test. |
| `durable-objects-15-chatroom` | Durable Objects + WebSockets | Runnable/browser-verifiable | verifier listed for page | 3.2 | Real chatroom page and DO WebSocket room. Needs automated WebSocket client verification. |

## Current verified set

The following have been run and passed in this workspace:

```bash
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
uv run python scripts/verify_examples.py kv-02-binding
uv run python scripts/verify_examples.py durable-objects-07-counter
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
2. Add `KVNamespace.iter_keys()` and route verification for KV listing.
3. Add D1 setup automation to `scripts/verify_examples.py`.
4. Add `WorkflowInstance` and `DurableObjectRef` typed handles.
5. Replace `htmlrewriter-11-opengraph` simplified HTML with real HTMLRewriter usage.
6. Add deterministic WebSocket verification for the chatroom.
7. Turn `ai-05-langchain` into a real working LangChain-compatible example or drop it from the verified set.
