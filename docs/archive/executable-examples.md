# Executable Examples Status

Last reviewed: 2026-05-01.

The examples are intended to be real Workers projects, not just snippets. Each example directory includes a `wrangler.jsonc`, `package.json`, `pyproject.toml`, `README.md`, and Python entrypoint unless the example intentionally includes a TypeScript client as well.

## Local smoke verification

List verifiable examples:

```bash
uv run python scripts/verify_examples.py --list
```

Run one example and perform HTTP checks:

```bash
uv run python scripts/verify_examples.py examples/start/hello-worker
uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage
uv run python scripts/verify_examples.py examples/start/fastapi-worker
uv run python scripts/verify_examples.py examples/storage-data/d1-database
uv run python scripts/verify_examples.py examples/state-events/durable-object-counter
uv run python scripts/verify_examples.py examples/start/static-assets
uv run python scripts/verify_examples.py examples/state-events/queues-producer-consumer
uv run python scripts/verify_examples.py examples/streaming/binary-response
uv run python scripts/verify_examples.py examples/network-edge/htmlrewriter-opengraph
uv run python scripts/verify_examples.py examples/state-events/cron-trigger
```

The verifier starts `uv run pywrangler dev`, waits for the local server, sends requests, checks status/body expectations, and shuts Wrangler down. `pywrangler` may call Wrangler internally, but users do not need an npm workflow for Python examples.

## Validation performed locally

```bash
uv run ruff check .
uv run python -m compileall -q examples/start/hello-worker examples/storage-data/kv-namespace examples/start/fastapi-worker \
  examples/storage-data/d1-database examples/ai-agents/langchain-style-chain examples/start/static-assets examples/state-events/durable-object-counter \
  examples/state-events/cron-trigger examples/ai-agents/workers-ai-inference examples/state-events/workflows-pipeline \
  examples/network-edge/htmlrewriter-opengraph examples/streaming/binary-response examples/network-edge/service-bindings-rpc \
  examples/network-edge/outbound-websocket-consumer examples/state-events/durable-object-chatroom examples/storage-data/r2-object-storage tests
uv run pytest -q
```

Current static result:

```text
All checks passed!
3 passed
```

Wrangler smoke checks actually run in this workspace:

```bash
uv run python scripts/verify_examples.py examples/start/hello-worker
uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage
uv run python scripts/verify_examples.py examples/storage-data/kv-namespace
uv run python scripts/verify_examples.py examples/start/fastapi-worker
uv run python scripts/verify_examples.py examples/storage-data/d1-database
uv run python scripts/verify_examples.py examples/state-events/durable-object-counter
uv run python scripts/verify_examples.py examples/start/static-assets
uv run python scripts/verify_examples.py examples/state-events/queues-producer-consumer
uv run python scripts/verify_examples.py examples/streaming/binary-response
uv run python scripts/verify_examples.py examples/network-edge/htmlrewriter-opengraph
uv run python scripts/verify_examples.py examples/state-events/cron-trigger
```

Verified results included successful HTTP checks for Worker responses, R2 put/get and JPEG byte comparison, KV text/JSON/list/delete, FastAPI ASGI routing, D1 local setup plus seeded and parameter-bound queries, Durable Object counter isolation, static asset plus dynamic route serving, queue producer enqueue, generated image response, OpenGraph HTML output, and scheduled Worker health.

## Literate programming style

The examples now favor comments that explain platform decisions instead of restating syntax. Examples:

- why static assets should not wake Python;
- why R2 streams should often remain JavaScript-native;
- why Durable Objects are used for WebSocket coordination;
- why Pyodide `create_proxy()` is needed for JavaScript event listeners;
- why service wrappers keep Worker entrypoints thin and testable.

## Remaining runtime caveat

Some examples require Cloudflare resources to be created before deployment:

- KV namespace IDs;
- D1 database IDs and migrations;
- R2 bucket;
- Durable Object migrations;
- Workers AI binding;
- Workflows binding;
- service-binding deployment order.

The examples are executable local projects. Resource IDs marked `REPLACE_WITH_*` can work in Wrangler local mode for some bindings, but must be replaced for deployed runs.
