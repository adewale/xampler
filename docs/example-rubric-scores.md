# Pythonic Rubric Scores for Examples

Last reviewed: 2026-05-01. Python anchor: Python 3.13.

Scores use [`docs/pythonic-rubric.md`](pythonic-rubric.md), including the newer criteria from Python S3 library research: familiar Python metaphors, layered API ergonomics, context managers where useful, typed dataclasses, iteration, and explicit `.raw` escape hatches.

## Summary table

| Example | Cloudflare primitive demonstrated | Score | Notes |
|---|---|---:|---|
| `workers-01-hello` | Workers request/response | 8.0 | Very small, readable, explicit response helper. Limited because there is little API surface to model. |
| `kv-02-binding` | Workers KV binding | 8.8 | Strong service/resource handle split: `KVNamespace` and `KVKey`; text/JSON/list/delete helpers; `exists`; native values. Needs fuller metadata/cache/TTL examples. |
| `fastapi-03-framework` | Python framework on Workers | 7.5 | Good Python-native framework shape. Thin example; needs docs on Pyodide constraints and cold start/package tradeoffs. |
| `d1-04-query` | D1 database | 8.7 | `D1Database`, `D1Statement`, `statement()`, parameter binding, `one_as(Quote)`, typed `Quote`, D1 null conversion. Needs transactions, retries, indexes, and migrations docs. |
| `ai-05-langchain` | Python package/AI orchestration shape | 6.75 | Safer than the broken upstream example because it isolates LangChain behind a service boundary, but currently illustrative rather than full. |
| `assets-06-static-assets` | Workers Assets | 8.9 | Very Pythonic because it teaches what *not* to do: do not wake Python for static files; `/api/status` demonstrates the dynamic boundary. Minimal code, strong platform fit. |
| `durable-objects-07-counter` | Durable Objects | 8.6 | Clear counter object with typed `CounterRef`, namespace wrapper, and named-object isolation verification. Needs Pythonic storage wrapper and concurrent state tests. |
| `scheduled-08-cron` | Cron triggers / scheduled Workers | 8.0 | Small `ScheduledJob` service. Needs typed event wrapper and test strategy for scheduled handlers. |
| `workers-ai-09-inference` | Workers AI | 8.25 | Typed request dataclass and `AIService.generate_text()`. Needs typed response models and model catalog docs. |
| `workflows-10-pipeline` | Workflows | 7.5 | Shows workflow class and instance creation. Needs more Pythonic `WorkflowService`/`WorkflowInstance` wrappers. |
| `htmlrewriter-11-opengraph` | HTMLRewriter | 7.75 | Uses metadata dataclass and clean route. Needs real `HTMLRewriter` boundary wrapper instead of simplified HTML generation. |
| `images-12-generation` | Binary responses | 8.2 | Dependency-free PNG bytes keep the example focused on binary Worker responses. Needs typed options and cache/R2 integration. |
| `service-bindings-13-rpc` | Service bindings / RPC | 8.0 | Python RPC method is simple and typed. Needs full TS client binding config and request/response dataclasses. |
| `websockets-14-stream-consumer` | WebSockets | 7.75 | Executable Durable Object WebSocket consumer with literate comments, alarm reconnection, and JS proxy boundary notes. Could still use a higher-level session wrapper. |
| `durable-objects-15-chatroom` | Durable Objects + WebSockets | 8.0 | Executable chatroom with WebSocket hibernation API, room routing, history, and browser client. Needs richer `ChatSession` abstraction and tests. |
| `queues-16-producer-consumer` | Queues | 8.5 | Typed `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueBatchResult`, producer wrapper, and explicit consumer ack/retry handling. Needs consumer verifier. |
| `r2-01` | R2 object storage | 9.25 | Most mature example: dataclasses, typed options, streaming, multipart `async with`, iteration, `.raw` escape hatch, object handle API, and route tests. |

## Overall average

**8.2 / 10** across the current set.

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
