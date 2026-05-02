# Composite Example Backlog

Last reviewed: 2026-05-02.

These are example ideas that combine existing Tier 1 primitives for common application tasks. This is a backlog only; do not implement these until the single-primitive examples stay healthy.

| Proposed example | Common task | Primitive mix | What it should prove |
|---|---|---|---|
| `app-27-support-agent` | Customer-support knowledge agent | Agents SDK, Workers AI, Vectorize, R2, D1, Queues, Email Workers | Ingest docs, search/vector-rank answers, accept email tickets, queue follow-up jobs, persist conversations. |
| `app-28-document-intelligence` | Upload, OCR/summarize, and search documents | R2, Queues, Workflows, Workers AI, Vectorize, D1, Browser Rendering | Durable async processing pipeline from upload to searchable summaries. |
| `app-29-product-analytics` | Event analytics dashboard | Workers, Analytics Engine, D1, R2, Hyperdrive, Pages/Assets | Capture events at edge, aggregate/query, serve dashboard. |
| `app-30-media-pipeline` | Image/video processing workflow | R2, Cloudflare Images, Stream, Queues, Workflows, D1 | Upload assets, transform/generate variants, track processing status. |
| `app-31-realtime-collab` | Chat/collaboration app | Durable Objects, WebSockets, D1, R2, Workers AI moderation, Queues | Room state, history, attachments, moderation, async notifications. |
| `app-32-saas-control-plane` | Multi-tenant SaaS backend | Workers for Platforms/Dispatch, D1, KV, R2, Secrets, Hyperdrive | Tenant routing, config/secrets, data isolation, customer extension points. |
| `app-33-data-lake-query` | Query a dataset lake | R2, R2 SQL, R2 Data Catalog, D1, Workflows, Queues | Publish cataloged data, run SQL, cache metadata, import summaries. |
| `app-34-secure-form-intake` | Public form with bot protection and workflow | Pages/Assets, Turnstile, Rate Limiting, Queues, D1, Email Workers | Validate users, throttle abuse, persist submissions, send notifications. |
| `app-35-observability-loop` | Production monitoring and incident summaries | Tail Workers, Logpush/Observability APIs, Queues, Workers AI, D1 | Collect logs/events, classify incidents, summarize and route alerts. |
| `app-36-postgres-edge-api` | Existing Postgres app at the edge | Hyperdrive, Workers, Cache API, D1, Queues | Read-through caching, Postgres access, background writes/jobs. |
