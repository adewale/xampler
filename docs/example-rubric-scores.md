# Pythonic Rubric Scores for Examples

Last reviewed: 2026-05-01. Python anchor: Python 3.13.

Scores use [`docs/pythonic-rubric.md`](pythonic-rubric.md), including the newer criteria from Python S3 library research: familiar Python metaphors, layered API ergonomics, context managers where useful, typed dataclasses, iteration, and explicit `.raw` escape hatches.

## Summary table

| Example | Cloudflare primitive demonstrated | Score | Notes |
|---|---|---:|---|
| `workers-01-hello` | Workers request/response | 3.2 | Very small, readable, explicit response helper. Limited because there is little API surface to model. |
| `kv-02-binding` | Workers KV binding | 3.4 | Strong service/resource handle split: `KVNamespace` and `KVKey`; text/JSON helpers; `exists`; native values. Needs reusable shared response module and fuller metadata/cache examples. |
| `fastapi-03-framework` | Python framework on Workers | 3.0 | Good Python-native framework shape. Thin example; needs docs on Pyodide constraints and cold start/package tradeoffs. |
| `d1-04-query` | D1 database | 3.3 | `D1Database.query()`/`query_one()`, typed `Quote`, D1 null conversion. Needs statement object, migrations docs, and richer error handling. |
| `ai-05-langchain` | Python package/AI orchestration shape | 2.7 | Safer than the broken upstream example because it isolates LangChain behind a service boundary, but currently illustrative rather than full. |
| `assets-06-static-assets` | Workers Assets | 3.5 | Very Pythonic because it teaches what *not* to do: do not wake Python for static files. Minimal code, strong platform fit. |
| `durable-objects-07-counter` | Durable Objects | 3.1 | Clear counter object. Needs Pythonic storage wrapper, typed methods, and more explicit state/lifecycle docs. |
| `scheduled-08-cron` | Cron triggers / scheduled Workers | 3.2 | Small `ScheduledJob` service. Needs typed event wrapper and test strategy for scheduled handlers. |
| `workers-ai-09-inference` | Workers AI | 3.3 | Typed request dataclass and `AIService.generate_text()`. Needs typed response models and model catalog docs. |
| `workflows-10-pipeline` | Workflows | 3.0 | Shows workflow class and instance creation. Needs more Pythonic `WorkflowService`/`WorkflowInstance` wrappers. |
| `htmlrewriter-11-opengraph` | HTMLRewriter | 3.1 | Uses metadata dataclass and clean route. Needs real `HTMLRewriter` boundary wrapper instead of simplified HTML generation. |
| `images-12-generation` | Python packages / binary responses | 3.2 | Pillow example is simple and Pythonic. Needs typed image options and cache/R2 integration. |
| `service-bindings-13-rpc` | Service bindings / RPC | 3.2 | Python RPC method is simple and typed. Needs full TS client binding config and request/response dataclasses. |
| `websockets-14-stream-consumer` | WebSockets | 3.1 | Executable Durable Object WebSocket consumer with literate comments, alarm reconnection, and JS proxy boundary notes. Could still use a higher-level session wrapper. |
| `durable-objects-15-chatroom` | Durable Objects + WebSockets | 3.2 | Executable chatroom with WebSocket hibernation API, room routing, history, and browser client. Needs richer `ChatSession` abstraction and tests. |
| `r2-01` | R2 object storage | 3.5 | Most mature example: dataclasses, typed options, streaming, multipart `async with`, iteration, `.raw` escape hatch. Needs object handle API and route tests. |

## Overall average

**3.23 / 4.0** across the current set.

The set is strongest where examples introduce a service object over a binding and Python-native methods: `r2-01`, `kv-02-binding`, `assets-06-static-assets`, `d1-04-query`, and `workers-ai-09-inference`.

The weakest examples are now `ai-05-langchain` and `workflows-10-pipeline`, mostly because they need deeper end-to-end workflows and tests rather than only the service-boundary shape.

## What would raise the scores

1. Add shared example infrastructure:
   - response helpers;
   - fake bindings;
   - route test helpers.
2. Add resource handles consistently:
   - `R2ObjectRef`;
   - `KVKey` already exists;
   - `D1Statement`;
   - `WorkflowInstance`;
   - `ChatSession`.
3. Add `async with` where lifecycle matters:
   - R2 multipart already has it;
   - D1 batch/transaction-like helpers if supported;
   - WebSocket sessions if useful.
4. Add route-level tests for all examples.
5. Expand the placeholder examples into runnable end-to-end demos, especially WebSockets, chatroom, Workflows, and Service Bindings.
