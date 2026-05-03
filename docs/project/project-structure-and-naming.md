# Project Structure and Naming

Last reviewed: 2026-05-02.

Xampler is a catalog of executable, Pythonic Cloudflare Developer Platform examples. Each example should teach:

1. the Cloudflare primitive;
2. a Pythonic wrapper/API surface;
3. how that wrapper compares to native Python Workers bindings;
4. a local verification path.

## Current structure

Examples now live under `examples/` by user journey, not by sequence number:

```text
examples/
  start/
    hello-worker/
    fastapi-worker/
    static-assets/
    pages-functions/
  storage-data/
    r2-object-storage/
    kv-namespace/
    d1-database/
    r2-sql/
    r2-data-catalog/
    hyperdrive-postgres/
  state-events/
    durable-object-counter/
    durable-object-chatroom/
    queues-producer-consumer/
    cron-trigger/
    workflows-pipeline/
  ai-agents/
    workers-ai-inference/
    ai-gateway-chat/
    vectorize-search/
    agents-sdk-tools/
    langchain-style-chain/
  network-edge/
    service-bindings-rpc/
    outbound-websocket-consumer/
    browser-rendering-screenshot/
    email-worker-router/
    htmlrewriter-opengraph/
  streaming/
    binary-response/
    gutenberg-stream-composition/
  full-apps/
    hvsc-ai-data-search/
```

## Naming rule

Use:

```text
<product-or-capability>-<hero-use-case>
```

Examples:

```text
r2-object-storage
d1-database
queues-producer-consumer
agents-sdk-tools
streaming-gutenberg-composition
hvsc-ai-data-search
```

Avoid sequence numbers. They imply tutorial order and make insertions/renames feel more important than they are.

## Documentation landing pages users need

| User journey | Doc |
|---|---|
| “What is this project?” | `README.md` |
| “Show me the API shape.” | `docs/api/unified-api-surface.md` |
| “Compare to native Python Workers.” | `docs/api/native-python-workers-comparison.md` |
| “Show streaming composition.” | `docs/data/streaming-api.md` + `examples/streaming/gutenberg-stream-composition` |
| “Which examples are verified?” | `docs/api/primitive-test-realism.md` |
| “What should be built next?” | `docs/project/complex-example-backlog.md` and `docs/project/unfinished-work.md` |

## Cloudflare docs grounding

Every example README should link directly to the relevant Cloudflare docs on `developers.cloudflare.com`, especially configuration/binding docs and product API references.
