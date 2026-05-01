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
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
uv run python scripts/verify_examples.py fastapi-03-framework
uv run python scripts/verify_examples.py d1-04-query
uv run python scripts/verify_examples.py durable-objects-07-counter
uv run python scripts/verify_examples.py assets-06-static-assets
uv run python scripts/verify_examples.py images-12-generation
uv run python scripts/verify_examples.py htmlrewriter-11-opengraph
uv run python scripts/verify_examples.py scheduled-08-cron
```

The verifier starts `uv run pywrangler dev`, waits for the local server, sends requests, checks status/body expectations, and shuts Wrangler down. `pywrangler` may call Wrangler internally, but users do not need an npm workflow for Python examples.

## Validation performed locally

```bash
uv run ruff check .
uv run python -m compileall -q workers-01-hello kv-02-binding fastapi-03-framework \
  d1-04-query ai-05-langchain assets-06-static-assets durable-objects-07-counter \
  scheduled-08-cron workers-ai-09-inference workflows-10-pipeline \
  htmlrewriter-11-opengraph images-12-generation service-bindings-13-rpc \
  websockets-14-stream-consumer durable-objects-15-chatroom r2-01 tests
uv run pytest -q
```

Current static result:

```text
All checks passed!
3 passed
```

Wrangler smoke checks actually run in this workspace:

```bash
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
uv run python scripts/verify_examples.py kv-02-binding
uv run python scripts/verify_examples.py fastapi-03-framework
uv run python scripts/verify_examples.py d1-04-query
uv run python scripts/verify_examples.py durable-objects-07-counter
uv run python scripts/verify_examples.py assets-06-static-assets
uv run python scripts/verify_examples.py images-12-generation
uv run python scripts/verify_examples.py htmlrewriter-11-opengraph
uv run python scripts/verify_examples.py scheduled-08-cron
```

Verified results included successful HTTP checks for Worker responses, R2 put/get and JPEG byte comparison, KV put/get, FastAPI ASGI routing, D1 local setup plus seeded-row query, Durable Object counter reset/increment/read, static asset serving, generated image response, OpenGraph HTML output, and scheduled Worker health.

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
