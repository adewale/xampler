# Cost-effective complex examples backlog

These examples should improve abstraction quality without forcing paid remote checks by default.

| Surface | Low-cost complex example | Why it helps |
|---|---|---|
| Browser Rendering | Render a local HTML report route, screenshot it, extract title/content, and compare PDF/content lengths. | Exercises multi-route realism without external browser targets. |
| R2 Data Catalog | Deterministic Iceberg namespace/table lifecycle plus schema fixture validation. | Makes table lifecycle semantics visible before real append/read. |
| Workflows | Workflow writes progress checkpoints to D1 and exposes `/timeline/<id>`. | Clarifies progress/state/retry vocabulary. |
| Agents | Tool-calling demo with deterministic calculator/search tools and transcript assertions. | Separates agent API from route/UI glue. |
| Email | Policy router with fixture messages: allow, reject, forward, annotate. | Produces a reusable `EmailRouter` shape. |
| HTMLRewriter | OpenGraph + canonical-link extractor over local fixture HTML. | Gives callback abstractions a second route beyond one metadata page. |
| Hyperdrive | Postgres-shaped fake transport plus SQL safety and connection-string diagnostics. | Improves API shape while real Hyperdrive remains credential/database blocked. |
| Durable Object/WebSocket | Room presence + replay log with two WebSocket clients and D1/R2 transcript export. | Avoids overfitting to a counter or simple chat echo. |

## Larger composite app ideas

These should wait until the lower-cost examples above are healthy.

| Proposed app | Primitive mix | What it should prove |
|---|---|---|
| Support agent | Agents SDK, Workers AI, Vectorize, R2, D1, Queues, Email Workers | Ingest docs, search/vector-rank answers, accept email tickets, queue follow-up jobs, persist conversations. |
| Document intelligence | R2, Queues, Workflows, Workers AI, Vectorize, D1, Browser Rendering | Durable async processing pipeline from upload to searchable summaries. |
| Realtime collaboration | Durable Objects, WebSockets, D1, R2, Workers AI moderation, Queues | Room state, history, attachments, moderation, async notifications. |
| Data lake query | R2, R2 SQL, R2 Data Catalog, D1, Workflows, Queues | Publish cataloged data, run SQL, cache metadata, import summaries. |
| Postgres edge API | Hyperdrive, Workers, Cache API, D1, Queues | Read-through caching, Postgres access, background writes/jobs. |
