# Unified Pythonic API Surface

Last reviewed: 2026-05-02.

The examples converge on one shape: Cloudflare bindings become small services, named resources become handles, inputs/results are dataclasses, long-running work exposes status, and every wrapper keeps `.raw` for platform escape hatches.

```python
# Bindings become services.
r2 = R2Bucket(env.BUCKET)
kv = KVNamespace(env.KV)
db = D1Database(env.DB)
queue = QueueService(env.QUEUE)
ai = AIService(env.AI)
agent = AgentSession(env.AGENT)

# Named things become handles.
obj = r2.object("datasets/hvsc/tracks.jsonl")
key = kv.key("profile:ada")
stmt = db.statement("SELECT * FROM tracks WHERE search_text LIKE ?")
run = workflows.instance("import-123")

# Inputs/results are dataclasses.
await obj.write_json(Track(...))
track = await stmt.one_as(Track, "%hubbard%")
await queue.send(IngestJob(...))
result: AgentRunResult = await agent.run("summarize jeroen tel tracks")

# Python protocols are preferred.
async for item in r2.iter_objects(prefix="datasets/"):
    ...

async with r2.multipart("large.bin") as upload:
    await upload.part(1, chunk)

# Long-running work exposes status.
status = await run.status()
progress = await pipeline.ingest_status()

# Escape hatch remains explicit.
raw = r2.raw
```

## Primitive hero surfaces

| Primitive | Smallest hero surface |
|---|---|
| Workers | `return json_response({"ok": True})` — tiny request/response entrypoint. |
| R2 | `async with bucket.multipart(key) as upload: ...`; `bucket.object(key).read_bytes()`; `async for obj in bucket.iter_objects(prefix)`. |
| KV | `kv.key(name).write_json(value)`; `await kv.key(name).read_json()`; `async for key in kv.iter_keys(prefix)`. |
| D1 | `db.statement(sql).bind(...).one_as(Model)`; indexed query plans; D1 null conversion at boundary. |
| FastAPI / ASGI | Normal `FastAPI()` routes behind a Worker `fetch()` adapter. |
| LangChain/package orchestration | `PromptChain(PromptTemplate(), DemoModel()).invoke(PromptInput(...))` behind `PromptService`. |
| Workers Assets | No Python for static files; Python only handles dynamic `/api/*`. |
| Durable Objects | `namespace.named("counter").increment()` routes to one stateful object. |
| Cron Triggers | `ScheduledJob.run(ScheduledEventInfo(...)) -> ScheduledRunResult`. |
| Workers AI | `ai.generate_text(TextGenerationRequest(...)) -> TextGenerationResponse`. |
| Workflows | `workflow.start(payload) -> WorkflowInstance`; `await instance.status()`. |
| HTMLRewriter | `OpenGraphRewriter(OpenGraphPage(...)).transform(html)`. |
| Binary responses | Worker returns deterministic PNG bytes with content type and binary verification. |
| Service Bindings / RPC | `await env.CODE.highlight_code(code)` exposed as a typed Python method. |
| Outbound WebSockets | Durable Object owns socket; `GET /demo/status` proves session/status shape. |
| Durable Objects + WebSockets | Room Durable Object owns sockets/history; `ChatMessage` is persisted and broadcast. |
| Queues | `queue.send(QueueJob(...), QueueSendOptions(...))`; consumer wraps `QueueMessage.ack()/retry()`. |
| Vectorize | `index.upsert([Vector(...)])`; `index.query(VectorQuery(...)) -> VectorQueryResult`. |
| Browser Rendering | `renderer.screenshot(ScreenshotRequest(...)) -> ScreenshotResult` or image bytes. |
| Email Workers | `EmailRouter.decide(IncomingEmail(...)) -> EmailDecision`; deployed path calls `forward()/setReject()`. |
| AI Gateway | `gateway.chat(ChatRequest(...))` with OpenAI-compatible messages plus demo transport. |
| R2 SQL | `client.query(R2SqlQuery(sql)).explain()` with read-only/single-table guards. |
| R2 Data Catalog | `catalog.list_namespaces()`; `catalog.list_tables(namespace) -> list[TableRef]`. |
| Pages | Static `public/` plus file-routed Functions, verified with `pages dev`. |
| HVSC AI/data app | `HvscPipeline` composes R2 + D1 + Queues + AI/vector seams with `ingest_status()`. |
| Hyperdrive | `HyperdrivePostgres(HyperdriveConfig.from_binding(env.HYPERDRIVE)).query(PostgresQuery(...))`. |
| Agents SDK | `AgentSession.run(message) -> AgentRunResult` with typed messages, tools, and Durable Object session routing. |
| Streaming composition | `ByteStream.iter_lines()` -> `JsonlReader.records()` -> `aiter_batches()` -> checkpointed sink. |

## Design rule

Every primitive should expose:

1. **Friendly Python surface** — handles, dataclasses, normal verbs.
2. **Cloudflare vocabulary** — bindings, queues, workflows, vectors, namespaces, tables.
3. **Status/progress** — for setup-dependent or long-running work.
4. **Deterministic demo transport** — local verification for account-backed APIs.
5. **`.raw` escape hatch** — direct access to the platform object/client.
