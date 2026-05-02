# Project Structure and Naming

Last reviewed: 2026-05-02.

## Current purpose

Xampler is a catalog of executable, Pythonic Cloudflare Developer Platform examples. Each example should teach:

1. the Cloudflare primitive;
2. a Pythonic wrapper/API surface;
3. how that wrapper compares to native Python Workers bindings;
4. a local verification path.

## Better naming scheme

The current product-first names are useful, but numbers no longer group related journeys. Recommended next scheme:

```text
examples/
  01-core/workers-hello/
  02-storage/r2-object-storage/
  02-storage/kv-namespace/
  02-storage/d1-database/
  03-state/durable-object-counter/
  03-state/durable-object-chatroom/
  04-streaming/gutenberg-stream-composition/
  05-ai/workers-ai-inference/
  05-ai/ai-gateway-chat/
  05-ai/agents-sdk-tools/
  06-data/r2-sql-query/
  06-data/r2-data-catalog-iceberg/
  06-data/hyperdrive-postgres/
  07-apps/hvsc-ai-data-search/
```

If we keep flat folders for GitHub browseability, use:

```text
workers-01-hello
r2-02-object-storage
kv-03-namespace
d1-04-database
streaming-27-gutenberg
agents-28-sdk
```

The key improvement is to reserve number ranges by journey: core, storage, state, streaming, AI, data, full apps.

## Documentation landing pages users need

| User journey | Doc |
|---|---|
| “What is this project?” | `README.md` |
| “Show me the API shape.” | `docs/unified-api-surface.md` |
| “Compare to native Python Workers.” | `docs/native-python-workers-comparison.md` |
| “Show streaming composition.” | `docs/streaming-api.md` + `streaming-27-gutenberg` |
| “Which examples are verified?” | `docs/primitive-test-realism.md` |
| “What should be built next?” | `docs/composite-example-backlog.md` |

## Cloudflare docs grounding

Every example README should link directly to the relevant Cloudflare docs on `developers.cloudflare.com`, especially configuration/binding docs and product API references.
