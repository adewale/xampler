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
| [`htmlrewriter-11-opengraph/`](htmlrewriter-11-opengraph) | HTMLRewriter | OpenGraph metadata model and edge HTML response shape. |
| [`images-12-generation/`](images-12-generation) | Python packages / binary responses | Pillow image generation from a Worker. |
| [`service-bindings-13-rpc/`](service-bindings-13-rpc) | Service bindings / RPC | Python RPC service shape with TypeScript client scaffold. |
| [`websockets-14-stream-consumer/`](websockets-14-stream-consumer) | WebSockets | WebSocket example scaffold and session model direction. |
| [`durable-objects-15-chatroom/`](durable-objects-15-chatroom) | Durable Objects + WebSockets | Chatroom durable object scaffold. |

## Pythonic API principles

See:

- [`docs/pythonic-rubric.md`](docs/pythonic-rubric.md)
- [`docs/cloudflare-python-api-shape.md`](docs/cloudflare-python-api-shape.md)
- [`docs/s3-python-library-research.md`](docs/s3-python-library-research.md)
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

## Requirements

- Node.js and npm
- Wrangler (`npx wrangler@latest ...` is used in the examples)
- Python 3.13+
- `uv` for local Python checks/tests
- A Cloudflare account for deployed resources

Python Workers are configured with the `python_workers` compatibility flag.

## Running checks

Static/local Python checks:

```bash
uv sync
uv run ruff check .
uv run pytest -q
```

Run and verify an example locally with Wrangler:

```bash
uv run python scripts/verify_examples.py --list
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
```
