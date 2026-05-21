# Capability matrix

Last reviewed: 2026-05-09.

Use this matrix with [`primitive-test-realism.md`](primitive-test-realism.md). Realism scores say how deeply an example is verified; these labels say what a specific operation promises.

| Label | Meaning |
|---|---|
| Supported | Implemented and verified for the documented runtime path. |
| Caveated | Works with documented limits such as credentials, public base URLs, buffering, consistency, or local-runtime differences. |
| Demo-only | Deterministic local shape is verified, but the real product call is not exercised by that path. |
| Remote-only | Requires deployed Cloudflare resources, credentials, or paid product usage; skipped by default. |
| Unsupported / throws | Intentionally unsupported; callers get an explicit error instead of silent no-op or ignored options. |
| Not covered | Not implemented or documented yet. |

## Stable storage/data surfaces

| Surface | Operation | Label | Notes |
|---|---|---|---|
| R2 | `put_text`, `put_bytes`, `put_stream`, `put` | Supported | Local Worker verifier writes text and binary fixture data through the binding. Small helpers may buffer; `put_stream` keeps large streams on the JS side. |
| R2 | `get_text`, `get_json`, `get_bytes`, `get`, `head`, `exists`, `delete` | Supported | Missing reads return `None`/`False` where documented. Binary download is byte-compared against a fixture. |
| R2 | `list`, `iter_objects` | Supported | Cursor pagination shape is exposed; local verifier covers listing. |
| R2 | `create_multipart_upload`, `resume_multipart_upload` | Caveated | API shape exists and uses `async with`; deeper completion/abort tests and remote verification remain pending. |
| R2 | public object URL | Caveated | Requires public bucket/custom domain/r2.dev URL outside the binding wrapper. Do not infer public URLs from keys. |
| R2 | signed download/upload URL | Unsupported / throws | A Workers R2 binding has no signing primitive. Use S3-compatible HTTP credentials or an explicit REST/S3 helper when added. |
| R2 | CORS, lifecycle, event notifications | Not covered | Use `.raw` or Cloudflare/Wrangler configuration. |
| KV | text/JSON read/write, `exists`, `delete` | Supported | Local verifier covers text, JSON, delete, and missing-key behavior. |
| KV | `list`, `iter_keys` | Supported | Local verifier covers list shape. |
| KV | metadata, expiration/cache TTL | Caveated | TTL write option exists for simple writes; richer metadata/cache behavior is not yet verified. |
| KV | deployed namespace semantics | Remote-only | Not part of default local checks. |
| D1 | statements, bound params, `one`, `all`, `first`, `one_as`, `execute`, `batch_run` | Supported | Local verifier initializes D1, queries seeded data, and checks query plan/index use. |
| D1 | migrations/transactions/retries | Not covered | Use Wrangler/native D1 paths or `.raw` until wrapper coverage expands. |
| Queues | `send`, `send_json`, `send_many` | Supported | Local verifier covers producer enqueue shape. |
| Queues | consumer `ack`, `retry`, backoff, DLQ decision logic | Supported | Deterministic local consumer harness verifies behavior. |
| Queues | real delivery and DLQ | Remote-only | Prepared `queues-dlq` profile verifies real queue/DLQ delivery remotely. |
| Vectorize | `upsert`, `query`/`search`, `query_by_id`, `get`, `delete`, `describe` | Supported | Local deterministic search and prepared remote profile cover core binding behavior. |
| Vectorize | metadata indexes and large batch helpers | Not covered | Future wrapper work. |

## REST-backed and account-backed surfaces

| Surface | Operation | Label | Notes |
|---|---|---|---|
| Workers AI | text generation | Caveated | Local path uses `DemoAIService`; prepared remote profile calls a real Workers AI binding and may incur usage. |
| Browser Rendering | screenshot/content/PDF/scrape REST routes | Remote-only | Local demo validates typed shape; prepared remote profile requires account/token and may incur usage. |
| AI Gateway | OpenAI-compatible chat | Caveated | Local demo validates shape; real route needs account, gateway, provider key, and opt-in remote verification. |
| R2 SQL | read-only `SELECT`/`SHOW`/`EXPLAIN` | Caveated | Local demo verifies query shaping; prepared remote profile calls real endpoint. Mutations and joins are unsupported by example guards. |
| R2 Data Catalog | namespace/table list and temporary lifecycle | Caveated | Local fixture validates shape; prepared remote profile exercises real Iceberg REST lifecycle. |
| Hyperdrive | config/demo query shape | Demo-only | Real Postgres client wiring and remote verification are not complete. |

## Events, actors, and network surfaces

| Surface | Operation | Label | Notes |
|---|---|---|---|
| Durable Objects | named refs, storage-backed counter, WebSocket room routes | Supported | Local verifier covers named-object isolation and chatroom state; remote WebSocket profile is opt-in. |
| Workflows | start/status shape | Caveated | Local deterministic status is verified; real runtime status verification needs deeper coverage. |
| Cron | scheduled handler shape | Supported | Local scheduled endpoint is exercised. Persistent side effects are not yet covered. |
| Service Bindings/RPC | Python provider + TS consumer | Caveated | Local two-worker path and prepared remote profile exist; richer auth/error patterns remain. |
| Outbound WebSockets | status/reconnect shape | Demo-only | Real outbound stream path is retained but not fully simulated locally. |
| Email Workers | inspect/forward/reject policy | Demo-only | HTTP policy route is verified; real Email Routing event verification remains future work. |
| HTMLRewriter | OpenGraph transform wrapper | Caveated | Typed escaping/output verified; real Python-native `HTMLRewriter` support is pending. |
| Agents | deterministic agent session and tool-call shapes | Demo-only | Direct Cloudflare Agents SDK interop and human-in-the-loop persistence remain future work. |

## Agent-tool safety contract

Storage/data tools should follow this default:

- read tools (`list`, `head`, `read`, safe `query`) do not require approval;
- write/delete/copy/upload/mutation tools require approval by default;
- `read_only=True` removes mutating tools entirely;
- validation errors should be model-visible structured payloads;
- provider/auth/conflict failures should preserve a stable code and original cause where possible.
