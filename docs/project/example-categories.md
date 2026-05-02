# Example Categories

Xampler examples are grouped by user journey in `examples/`, but they also fall into realism and product categories.

## Best local/no-lies examples

These are the safest starting points. The local verifier exercises the real local primitive path rather than only a deterministic product stand-in.

- `examples/start/hello-worker`
- `examples/start/static-assets`
- `examples/start/pages-functions`
- `examples/storage-data/r2-object-storage`
- `examples/storage-data/kv-namespace`
- `examples/storage-data/d1-database`
- `examples/state-events/durable-object-counter`
- `examples/state-events/durable-object-chatroom`
- `examples/state-events/cron-trigger`
- `examples/state-events/queues-producer-consumer`
- `examples/network-edge/service-bindings-rpc/ts`
- `examples/streaming/binary-response`
- `examples/streaming/gutenberg-stream-composition`

## Local deterministic demo seams

These examples preserve the real product route or binding shape, but local verification uses a deterministic `/demo` or harness because the product is account-backed, deployed-only, or unsupported by local Wrangler.

- `examples/ai-agents/workers-ai-inference`
- `examples/ai-agents/ai-gateway-chat`
- `examples/ai-agents/vectorize-search`
- `examples/ai-agents/agents-sdk-tools`
- `examples/ai-agents/langchain-style-chain`
- `examples/state-events/workflows-pipeline`
- `examples/network-edge/browser-rendering-screenshot`
- `examples/network-edge/email-worker-router`
- `examples/network-edge/outbound-websocket-consumer`
- `examples/storage-data/r2-sql`
- `examples/storage-data/r2-data-catalog`
- `examples/storage-data/hyperdrive-postgres`
- `examples/full-apps/hvsc-ai-data-search` for AI/Vectorize seams; its R2/D1 paths are real locally.

## Remote/paid/account-backed examples

These need Cloudflare credentials, deployed URLs, product entitlements, or prepared account resources for full realism. See [`../runtime/remote-verification.md`](../runtime/remote-verification.md). Several profiles now have explicit preparation paths in `scripts/prepare_remote_examples.py` so users can rely on `wrangler login` plus product-specific tokens instead of manually copying deployed URLs.

- Workers AI
- AI Gateway
- Vectorize
- Browser Rendering
- Hyperdrive
- R2 SQL
- R2 Data Catalog
- Cloudflare Images
- Workers Analytics Engine
- deployed Queues/DLQ
- deployed Service Bindings
- deployed WebSockets

## Composition examples

These are best for seeing primitives compose rather than stand alone.

- `examples/streaming/gutenberg-stream-composition` — R2 object body stream, ZIP reading, byte/text/line/record streams, batches, checkpoints, AI/agent/WebSocket event shapes.
- `examples/full-apps/hvsc-ai-data-search` — R2 datasets, streaming JSONL shard ingestion, D1 state/search, Queue jobs, AI/Vectorize seams, interactive browser progress.
- `examples/network-edge/service-bindings-rpc/ts` — two local Workers; TypeScript Worker invokes Python Worker through a Service Binding.
- `examples/state-events/durable-object-chatroom` — Durable Object state plus true WebSocket broadcast verification.

## By product family

| Family | Examples |
|---|---|
| Start | `hello-worker`, `fastapi-worker`, `static-assets`, `pages-functions` |
| Storage/data | `r2-object-storage`, `kv-namespace`, `d1-database`, `r2-sql`, `r2-data-catalog`, `hyperdrive-postgres` |
| State/events | `durable-object-counter`, `durable-object-chatroom`, `queues-producer-consumer`, `cron-trigger`, `workflows-pipeline` |
| AI/agents | `workers-ai-inference`, `ai-gateway-chat`, `vectorize-search`, `agents-sdk-tools`, `langchain-style-chain` |
| Network/edge | `service-bindings-rpc`, `outbound-websocket-consumer`, `browser-rendering-screenshot`, `email-worker-router`, `htmlrewriter-opengraph` |
| Streaming | `binary-response`, `gutenberg-stream-composition` |
| Full apps | `hvsc-ai-data-search` |
