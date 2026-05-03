# Remaining Gaps Explained

Last reviewed: 2026-05-02.

This explains the main gaps called out in the original-goals audit and what each one means in practical terms.

## Remote verification for account-backed products

Many Cloudflare products cannot be fully exercised by local Miniflare/Wrangler alone. Browser Rendering, AI Gateway, Workers AI, Vectorize, R2 SQL, R2 Data Catalog, Hyperdrive, Email Routing, and Agents-like flows all need real account resources, tokens, indexes, gateways, databases, routes, or paid/product entitlements.

Xampler now uses three verification layers:

1. **Deterministic local demo transport** — proves our Python API shape, dataclasses, validation, and response handling.
2. **Real route retained** — keeps the actual Cloudflare binding/API vocabulary in the example.
3. **Env-gated remote preparation and verification** — `scripts/prepare_remote_examples.py` creates resources/deploys Workers where possible, and `scripts/verify_remote_examples.py` calls the real deployed route.

Prepared profiles now cover Vectorize, Queues/DLQ, Service Bindings, Durable Object WebSockets, Browser Rendering, R2 SQL, and R2 Data Catalog. REST-backed products still require explicit product tokens during preparation, stored with `wrangler secret put` rather than committed files.

Remaining work:

- run token-backed profiles in CI/secrets;
- add product-specific metadata assertions, not just HTTP 200;
- run cleanup for disposable remote resources when a test run is complete;
- finish AI Gateway, Hyperdrive, Images, Analytics Engine, and richer R2 table data assertions.

## Real R2 zip streaming and unzipping

The Gutenberg golden file is real and lives in R2:

```text
r2://xampler-datasets/gutenberg/100/raw/pg100-h.zip
```

The current streaming example demonstrates the desired stream vocabulary with sample text:

```python
ByteStream.iter_lines() -> JsonlReader.records() -> aiter_batches() -> sink
```

What is missing is using the actual R2 object body as the source and, where feasible, unzipping it into records inside the Worker.

There are two hard constraints:

- Python Workers run in WebAssembly memory; loading a large archive into Python bytes can double memory use and crash.
- Zip libraries may require seekable file-like objects or buffering, which is not the same as true streaming unzip.

The right next step is not “read the zip into bytes.” It is:

1. expose R2 body as a JS/Python chunk stream;
2. test whether a Pyodide-compatible zip reader can consume bounded chunks or a spooled file;
3. checkpoint extracted files/records;
4. write extracted text/catalog records to R2/D1/Vectorize in batches;
5. bypass Python entirely when serving the zip back to users.

In short: Python should process bounded chunks and records; large binary serving should use R2/JS streams directly.

## Missing Cache, Analytics, and Images examples

These gaps are important because they represent common production tasks that are not covered by current examples.

| Missing product | Why it matters | Likely example |
|---|---|---|
| Cache API | Edge caching is one of the most common Workers use cases. It also interacts with streaming and large binary guidance. | `examples/network-edge/cache-api-response` or `examples/start/cache-api` |
| Workers Analytics Engine | Production apps need event telemetry and aggregate analytics. It would pair naturally with HVSC search events. | `examples/storage-data/analytics-engine-events` |
| Cloudflare Images | Current binary response example is not the Cloudflare Images product. Images needs upload/transform/delivery API coverage. | `examples/streaming/cloudflare-images-transform` or `examples/network-edge/cloudflare-images-api` |

The current `examples/streaming/binary-response` should remain, but it should never be described as Cloudflare Images coverage.

## Recently closed gaps

| Gap | What changed | Remaining caveat |
|---|---|---|
| Direct Cloudflare docs links | Every example README now has a `Cloudflare docs` section with product links. | Keep links current as products move. |
| Full local and deployed Service Bindings verifier | `verify_examples.py examples/network-edge/service-bindings-rpc/ts` starts the Python provider and TypeScript consumer locally; remote prep deploys Python provider first, TS consumer second, then verifies deployed Service Binding RPC. | Add richer RPC payload/error compatibility checks. |
| True local and deployed WebSocket broadcast verifier | Chatroom verifier opens two real WebSocket clients locally; remote prep deploys the Durable Object Worker and verifies broadcast against the deployed URL. | Add hibernation/reconnect persistence checks. |
| Queue retry/DLQ semantics | Queue verifier checks producer, consumer ack/retry, and deterministic dead-letter decision; remote prep creates queues/DLQ, deploys the Worker, sends a failing job, and polls a Durable Object tracker until DLQ delivery is observed. | Add batch/concurrency assertions and optional message cleanup. |
| Direct R2 object-body unzip | Gutenberg `/zip-demo` reads the R2 object's `ReadableStream`, buffers the streamed zip bytes for Python `zipfile`, and reads the first HTML entry. | Python `zipfile` still needs a seekable buffer for the central directory; a true non-seekable ZIP parser would require a different library/format constraint. |

## Library surface migration is underway, but not complete for every product

The stable wrapper pattern has moved from examples into importable `xampler` modules. Examples now demonstrate library usage instead of being the only place the product API exists.

Shared library modules now include:

```text
xampler.ai
xampler.browser_rendering
xampler.cloudflare
xampler.d1
xampler.kv
xampler.queues
xampler.r2
xampler.r2_data_catalog
xampler.r2_sql
xampler.response
xampler.status
xampler.streaming
xampler.types
xampler.vectorize
```

What still belongs in examples:

- HTTP route handlers;
- HTML/browser UI;
- verifier-only endpoints;
- app-specific pipeline orchestration;
- product surfaces that still mix setup, UI, and runtime behavior too tightly.

Remaining migration candidates include Durable Object refs, Workflows, Hyperdrive, AI Gateway, Agents, Email, and HTMLRewriter. The principle has changed from “do not move product wrappers too early” to “make reusable product APIs importable, while keeping route/demo/app glue local.”
