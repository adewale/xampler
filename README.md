# Xampler

Python Workers examples for people who know Python and are learning the Cloudflare Developer Platform.

These examples use [`cfboundary`](https://github.com/adewale/cfboundary) where low-level JavaScript/Python conversion matters: `JsProxy` conversion, Python `bytes` to JavaScript `Uint8Array`, JavaScript `null`/`undefined`, and stream handling.

## Naming convention

Example directories put the Cloudflare product or primitive first, then the number:

```text
r2-01/
kv-02-binding/
d1-04-query/
```

## Examples

| Example | Primitive / topic | What it demonstrates |
|---|---|---|
| [`workers-01-hello/`](workers-01-hello) | Workers | Minimal Python Worker and response helper. |
| [`r2-01/`](r2-01) | R2 | Pythonic object storage wrapper, metadata, listing, streaming, multipart. |
| [`kv-02-binding/`](kv-02-binding) | Workers KV | `KVNamespace`/`KVKey`, text/JSON values, existence, delete, list. |
| [`fastapi-03-framework/`](fastapi-03-framework) | FastAPI on Workers | Python framework shape on Workers. |
| [`d1-04-query/`](d1-04-query) | D1 | Query wrapper, typed rows, D1 null/boundary conversion. |
| [`ai-05-langchain/`](ai-05-langchain) | Python package / LangChain shape | Keeps package orchestration behind a service boundary. |
| [`assets-06-static-assets/`](assets-06-static-assets) | Workers Assets | Serve static files without waking Python. |
| [`durable-objects-07-counter/`](durable-objects-07-counter) | Durable Objects | Stateful counter object. |
| [`scheduled-08-cron/`](scheduled-08-cron) | Cron triggers | Scheduled handler with job service object. |
| [`workers-ai-09-inference/`](workers-ai-09-inference) | Workers AI | Typed request dataclass and AI service wrapper. |
| [`workflows-10-pipeline/`](workflows-10-pipeline) | Workflows | Workflow entrypoint and instance creation. |
| [`queues-16-producer-consumer/`](queues-16-producer-consumer) | Queues | Producer/consumer wrapper, typed jobs, ack/retry. |
| [`vectorize-17-search/`](vectorize-17-search) | Vectorize | Typed vectors, upsert, query, get, delete, describe. |
| [`browser-rendering-18-screenshot/`](browser-rendering-18-screenshot) | Browser Rendering | REST screenshot client from a Python Worker. |
| [`email-workers-19-router/`](email-workers-19-router) | Email Workers | Inspect, reject, and forward incoming email. |
| [`ai-gateway-20-universal/`](ai-gateway-20-universal) | AI Gateway | OpenAI-compatible chat through AI Gateway. |
| [`r2-sql-21-query/`](r2-sql-21-query) | R2 SQL | SQL query client wrapper. |
| [`r2-data-catalog-22-iceberg/`](r2-data-catalog-22-iceberg) | R2 Data Catalog | Iceberg REST namespace/table client. |
| [`pages-23-functions/`](pages-23-functions) | Pages | Static Pages project with file-based Function. |
| [`htmlrewriter-11-opengraph/`](htmlrewriter-11-opengraph) | HTMLRewriter | OpenGraph metadata model and edge HTML response shape. |
| [`images-12-generation/`](images-12-generation) | Python packages / binary responses | Pillow image generation from a Worker. |
| [`service-bindings-13-rpc/`](service-bindings-13-rpc) | Service bindings / RPC | Python RPC service shape with TypeScript client scaffold. |
| [`websockets-14-stream-consumer/`](websockets-14-stream-consumer) | WebSockets | WebSocket example scaffold and session model direction. |
| [`durable-objects-15-chatroom/`](durable-objects-15-chatroom) | Durable Objects + WebSockets | Chatroom durable object scaffold. |

## Pythonic API principles

See:

- [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md)
- [`docs/pythonic-rubric.md`](docs/pythonic-rubric.md)
- [`docs/cloudflare-python-api-shape.md`](docs/cloudflare-python-api-shape.md)
- [`docs/s3-python-library-research.md`](docs/s3-python-library-research.md)
- [`docs/api-iteration-log.md`](docs/api-iteration-log.md)
- [`docs/primitives-api-surface.md`](docs/primitives-api-surface.md)
- [`docs/python-design-patterns.md`](docs/python-design-patterns.md)
- [`docs/top-10-improvement-plan.md`](docs/top-10-improvement-plan.md)
- [`docs/primitive-test-realism.md`](docs/primitive-test-realism.md)
- [`docs/pythonic-tooling.md`](docs/pythonic-tooling.md)
- [`docs/cloudflare-primitives-pythonic-scores.md`](docs/cloudflare-primitives-pythonic-scores.md)
- [`docs/example-rubric-scores.md`](docs/example-rubric-scores.md)
- [`docs/examples-status-and-pythonicness.md`](docs/examples-status-and-pythonicness.md)
- [`docs/executable-examples.md`](docs/executable-examples.md)

The short version:

1. Wrap each Cloudflare binding in a small service object.
2. Use resource handles where that matches Python expectations.
3. Return native Python values and dataclasses.
4. Keep `cfboundary` conversion at the JS/Python boundary.
5. Use `async for` for pagination/streams and `async with` for lifecycles.
6. Keep `.raw` as an explicit escape hatch.

## Primitive metrics

Coverage and Pythonic API scores are out of 10. Test realism is out of 5; see [`docs/primitive-test-realism.md`](docs/primitive-test-realism.md).

| Primitive | Coverage / 10 | Pythonic API / 10 | Test Realism / 5 |
|---|---:|---:|---:|
| R2 object storage | 8.5 | 9.25 | 4 |
| Workers Assets | 7.0 | 8.75 | 3 |
| Workers KV | 7.5 | 8.5 | 3 |
| D1 database | 6.8 | 8.5 | 3 |
| Durable Objects | 6.5 | 8.25 | 3 |
| Workers AI | 5.5 | 8.25 | 1 |
| Queues | 7.5 | 8.25 | 1 |
| FastAPI / ASGI | 6.0 | 8.0 | 3 |
| Cron Triggers | 6.0 | 8.0 | 2 |
| Binary responses / Pillow | 6.0 | 8.0 | 3 |
| Service Bindings / RPC | 6.0 | 8.0 | 1 |
| Durable Objects + WebSockets | 7.0 | 8.0 | 1 |
| Vectorize | 7.2 | 8.25 | 1 |
| Pages | 5.0 | 8.0 | 1 |
| Workflows | 6.5 | 7.75 | 1 |
| HTMLRewriter | 4.5 | 7.75 | 2 |
| Outbound WebSockets | 6.5 | 7.75 | 1 |
| Browser Rendering | 5.0 | 7.75 | 1 |
| Email Workers | 5.5 | 7.75 | 1 |
| AI Gateway | 5.0 | 7.75 | 1 |
| R2 Data Catalog | 5.0 | 7.75 | 1 |
| R2 SQL | 4.5 | 7.5 | 1 |
| LangChain/package orchestration | 3.0 | 6.75 | 1 |

## Requirements

- Python 3.13+
- `uv` for dependency management, local Worker runs, checks, and tests
- Node.js available on PATH because Wrangler is a JavaScript tool under the hood
- A Cloudflare account for deployed resources

Python Workers are configured with the `python_workers` compatibility flag.

## Running checks

Static/local Python checks:

```bash
uv sync
uv run ruff check .
uv run pytest -q
```

Run and verify an example locally with `uv` + `pywrangler`:

```bash
uv run python scripts/verify_examples.py --list
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
```
