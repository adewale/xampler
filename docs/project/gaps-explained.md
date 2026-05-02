# Remaining Gaps Explained

Last reviewed: 2026-05-02.

This explains the main gaps called out in the original-goals audit and what each one means in practical terms.

## Remote verification for account-backed products

Many Cloudflare products cannot be fully exercised by local Miniflare/Wrangler alone. Browser Rendering, AI Gateway, Workers AI, Vectorize, R2 SQL, R2 Data Catalog, Hyperdrive, Email Routing, and Agents-like flows all need real account resources, tokens, indexes, gateways, databases, routes, or paid/product entitlements.

Xampler currently uses two verification layers:

1. **Deterministic local demo transport** — proves our Python API shape, dataclasses, validation, and response handling.
2. **Real route retained** — keeps the actual Cloudflare binding/API vocabulary in the example.

What is missing is a third layer:

```bash
uv run python scripts/verify_examples.py examples/ai-agents/ai-gateway-chat --remote
```

That remote profile should:

- require explicit environment variables such as `CLOUDFLARE_ACCOUNT_ID` or product-specific tokens;
- create or target known test resources;
- call the real deployed/local-remote binding route;
- assert product-specific metadata, not just HTTP 200;
- skip cleanly when credentials are absent.

Without this, Tier 1 examples are honest about API shape but not yet full proof that the account-backed Cloudflare product worked end to end.

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
| Full local Service Bindings verifier | `verify_examples.py examples/network-edge/service-bindings-rpc/ts` starts the Python provider and TypeScript consumer; TS invokes Python via Service Binding. | Still needs deployed verification. |
| True WebSocket broadcast verifier | Chatroom verifier opens two real WebSocket clients and checks broadcast delivery. | Still needs deployed verification. |
| Queue retry/DLQ semantics | Queue verifier checks producer, consumer ack/retry, and deterministic dead-letter decision. | Real deployed Queue DLQ routing still needs credentials/resources. |
| Direct R2 object-body unzip | Gutenberg `/zip-demo` reads the R2 object's `ReadableStream`, buffers the streamed zip bytes for Python `zipfile`, and reads the first HTML entry. | Python `zipfile` still needs a seekable buffer for the central directory; a true non-seekable ZIP parser would require a different library/format constraint. |

## Wrapper duplication not yet lifted into shared typed package

Most examples still define their own wrapper classes locally. That is intentional so examples remain self-contained and easy to read, but repeated patterns are now stable enough to start lifting.

Repeated patterns include:

- service wrappers around bindings;
- `.raw` escape hatch;
- dataclass request/result shapes;
- deterministic demo transports;
- status/progress results;
- stream/batch/checkpoint helpers;
- JSON/error response helpers.

What has already moved into shared code:

```text
xampler/streaming.py
```

What should move next, carefully:

| Candidate | Why |
|---|---|
| `xampler.response` | Avoid repeated response/content-type helpers. |
| `xampler.types` | Shared `Progress`, `OperationStatus`, `Checkpoint`, `JsonDict`. |
| `xampler.protocols` | `SupportsRaw`, `DemoTransport`, `RemoteVerifier`, stream protocols. |
| `xampler.cloudflare` | Tiny common base classes for service wrappers/handles, not product logic. |

What should **not** move too early:

- product-specific wrappers that are still changing quickly;
- code that hides Cloudflare vocabulary;
- anything that makes examples harder to understand when read alone.

The principle is: lift only boring, stable, repeated concepts. Keep hero product logic local until the API shape has proved itself in multiple examples.
