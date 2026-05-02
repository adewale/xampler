# Xampler API vs Native Python Workers

Last reviewed: 2026-05-02.

Native Python Workers expose Cloudflare bindings directly. Xampler adds a thin Pythonic layer on top while preserving `.raw` escape hatches.

| Hero use case | Native Python Workers shape | Xampler shape |
|---|---|---|
| R2 read/write | `await env.BUCKET.put(key, value)` | `await bucket.object(key).write_bytes(value)` |
| R2 streaming | `obj = await bucket.get(key); body = obj.body` | `async for chunk in obj.iter_bytes(): ...` |
| KV JSON | `json.loads(await env.KV.get(key))` | `await kv.key(key).read_json()` |
| D1 typed row | `await env.DB.prepare(sql).bind(x).all()` | `await db.statement(sql).bind(x).one_as(Model)` |
| Queues | `await env.QUEUE.send(dict)` | `await queue.send(QueueJob(...), QueueSendOptions(...))` |
| Workers AI | `await env.AI.run(model, dict)` | `await ai.generate_text(TextGenerationRequest(...))` |
| Vectorize | raw vector/query dictionaries | `Vector(...)`, `VectorQuery(...)`, `VectorQueryResult` |
| Durable Objects | `stub = ns.get(ns.idFromName(name))` | `await namespace.named(name).increment()` |
| Workflows | raw binding start/status calls | `instance = await workflow.start(payload); await instance.status()` |
| Agents | raw Durable Object/session route | `await AgentSession(raw).run(message)` |
| Browser Rendering | `fetch()` Cloudflare REST endpoint | `renderer.screenshot(ScreenshotRequest(...))` |
| AI Gateway | OpenAI-compatible JSON over `fetch()` | `gateway.chat(ChatRequest(...))` |
| Hyperdrive | binding-provided connection metadata | `HyperdrivePostgres(config).query(PostgresQuery(...))` |

Xampler should never hide the platform permanently. Each wrapper keeps Cloudflare vocabulary visible and exposes `.raw` when a product evolves faster than the wrapper.
