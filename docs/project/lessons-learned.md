# Lessons Learned

Last updated: 2026-05-02.

This project is building Pythonic, executable Cloudflare examples. These are the lessons learned so far.

## 1. Runnable beats plausible

A good example is not just code that looks right. It must run under the same local workflow a user will use.

What changed:

- Added `scripts/verify_examples.py`.
- Verified `examples/start/hello-worker`, `examples/storage-data/r2-object-storage`, `examples/storage-data/kv-namespace`, `examples/start/fastapi-worker`, `examples/storage-data/d1-database`, `examples/state-events/durable-object-counter`, `examples/start/static-assets`, `examples/state-events/queues-producer-consumer`, `examples/streaming/binary-response`, `examples/network-edge/htmlrewriter-opengraph`, and `examples/state-events/cron-trigger` at different realism levels.
- Added `docs/api/primitive-test-realism.md` to make test depth visible.

Lesson: every new example should ship with a verifier path, even if the first verifier is shallow. If the official Cloudflare example requires local setup, our verifier should automate that setup instead of merely documenting it.

## 2. `pywrangler` is the right user-facing tool for Python examples

Plain `wrangler dev` failed for examples that depend on Python packages because dependencies such as `cfboundary` were not vendored.

What changed:

- Example package scripts now use `uv run pywrangler dev` and `uv run pywrangler deploy`.
- Docs now prefer `uv` + `pywrangler` over `npm install` + `npx wrangler`.
- Added `docs/runtime/pythonic-tooling.md`.

Lesson: Node/Wrangler may exist under the hood, but the developer workflow should feel Python-native.

## 3. Pythonic means layered, not hidden

The most successful API shape has three layers:

1. Friendly Python layer: `read_text`, `write_json`, `exists`, `iter_*`.
2. Cloudflare platform layer: `put`, `get`, `query`, `send`, `upsert`, metadata/options.
3. Escape hatch: `.raw` or a low-level client for unwrapped APIs.

Lesson: do not hide Cloudflare concepts; provide a Pythonic path into them.

## 4. Resource handles make APIs feel natural

The S3 ecosystem taught us that Python developers like familiar metaphors: `pathlib`, `open`, `iter`, context managers, and file-like verbs.

What changed:

- R2 now has `bucket.object("key")` returning an `R2ObjectRef`.
- KV has `kv.key("name")` returning a `KVKey`.
- D1 has `db.statement(sql)` returning a `D1Statement`.

Lesson: named Cloudflare resources should usually have small Python handle objects.

## 5. Dataclasses are the right default for tutorial-facing structure

Raw service dictionaries are flexible but less teachable.

What changed:

- R2 uses dataclasses for metadata, ranges, conditionals, multipart parts.
- Queues uses `QueueJob`.
- Vectorize uses `Vector`, `VectorQuery`, `VectorMatch`, `VectorQueryResult`.
- Workers AI and AI Gateway use typed request dataclasses.

Lesson: use dataclasses for public example APIs, then convert to JS-shaped dictionaries at the boundary.

## 6. Convert at the boundary

Python Workers expose JavaScript APIs through Pyodide. Values can be `JsProxy`, JavaScript `null`, JavaScript `undefined`, or native JS streams.

What changed:

- `cfboundary` is used for `to_js`, `to_py`, `to_js_bytes`, `is_js_missing`, and stream conversion.
- R2 had a real bug where `dataclasses.asdict()` tried to deepcopy a `JsProxy`; the fix was to normalize `uploaded` metadata before returning `R2ObjectInfo`.

Lesson: never let raw JS values leak into dataclasses or business logic unless the field is explicitly `.raw`.

## 7. Binary and streaming examples are essential

String-only object storage examples are too shallow.

What changed:

- Added `examples/storage-data/r2-object-storage/fixtures/BreakingThe35.jpeg`.
- The R2 verifier uploads the JPEG, streams it back, and byte-compares the result.

Lesson: realistic binary fixtures expose boundary and streaming bugs that text examples miss.

## 8. Test realism needs its own metric

Coverage and Pythonic API design can look good while examples remain under-tested.

What changed:

- Added test realism levels from 0 to 5.
- README now shows coverage, Pythonic API, and test realism side by side.

Lesson: keep test realism visible so the repo does not drift into attractive but unverified samples.

## 9. Static Assets are most Pythonic when Python is not involved

For Workers Assets, the Pythonic/platform-correct move is to let the edge serve static files directly.

Lesson: sometimes the best Python API is no Python API.

## 10. Durable Objects need literate comments

Durable Objects are powerful but unfamiliar to many Python developers.

What changed:

- Counter, stream consumer, and chatroom examples explain why Durable Objects own state and WebSocket coordination.

Lesson: comments should explain platform surprises, not restate syntax.

## 11. The official examples are the baseline for trust

Cloudflare's official `python-workers-examples` are valuable because they are small, direct, and runnable.

Lesson: Xampler can be more Pythonic and broader, but must earn trust by matching or exceeding the official repo's run-and-verify discipline.

## 12. Top priority is improving the top 10 primitives

For average Python developers, the most important primitives are:

1. Workers
2. R2
3. D1
4. KV
5. Queues
6. Workers AI
7. Vectorize
8. Durable Objects
9. Assets / Pages
10. Cron Triggers

Lesson: improve coverage, Pythonic API, and test realism here before polishing long-tail products.

## 13. Best-practice docs are unevenly distributed

Cloudflare has explicit best-practice sections for some primitives, including Workers, D1, Durable Objects, Vectorize, and selected R2 docs. Other products have guidance spread across API/configuration/pattern docs rather than a single best-practices directory.

Lesson: best-practice support should be tracked per primitive, not assumed globally.

## 14. Complex examples expose composability gaps

The `examples/full-apps/hvsc-ai-data-search` example combines HVSC release metadata, R2, D1, Queues, Workers AI and Vectorize seams. It showed that each primitive wrapper needs typed inputs and outputs that compose with the next wrapper.

Lesson: keep the small examples focused, but regularly build one end-to-end app to discover missing API affordances.

## 15. Scoring must be actionable

Scores are useful only when they lead to concrete next steps.

What changed:

- Coverage and Pythonic API scores are out of 10.
- Test realism is out of 5.
- `docs/archive/top-10-improvement-plan.md` identifies the next action for each key primitive.

Lesson: every low score should point to the next PR.

## 16. Local and remote resource intent must be explicit

Wrangler can target local or remote resources, and the difference is easy to miss in long-running dataset scripts.

What changed:

- HVSC dataset upload scripts now default to remote Cloudflare R2.
- `--local` is opt-in for intentionally seeding Wrangler's local R2 store.
- The published HVSC catalog shards are verified in remote `xampler-datasets` before browser ingestion.

Lesson: data publication scripts should make production/remote intent explicit and should verify the exact bucket/prefix they expect later examples to consume.

## 17. Browser examples need product UX, not just endpoint buttons

The HVSC page initially had working endpoints, but search still felt broken because users saw raw JSON, had to know the setup order, and could trigger repeated output repainting.

What changed:

- The HVSC browser flow now has a stable progress indicator that avoids flashing large JSON blobs.
- Search renders result cards instead of only dumping API responses.
- Submitting a search before import automatically prepares the catalog and reruns the search.
- Shard import retries transient local Worker restarts.

Lesson: complex examples should guide the user through state transitions. If a feature depends on setup, the UI should either perform the setup or explain the exact next action in-place.

## 18. The shared API surface should be earned by reuse

Early on, many wrappers lived only inside individual examples. That was good for readability, but it made repeated ideas drift: status fields, JSON responses, stream helpers, demo transports, and `.raw` escape hatches all appeared with small differences.

What changed:

- Added `xampler.streaming` with `ByteStream`, `RecordStream`, `JsonlReader`, `aiter_batches`, `async_enumerate`, `StreamCheckpoint`, and `AgentEvent`.
- Added `xampler.status` with `OperationState`, `Progress`, `Checkpoint`, and `BatchResult`.
- Added `xampler.response` with `jsonable()` and `error_payload()`.
- Added `xampler.types` with `NewType` ids/keys, `SupportsRaw`, `DemoTransport`, and `RemoteVerifier`.
- Converted Gutenberg streaming and HVSC catalog ingestion to use `xampler.streaming`.
- Converted Workflows and Workers AI to use shared status/response/demo-transport ideas.

Lesson: do not extract whole product clients too early. Extract boring, repeated contracts first, then promote product wrappers only after several examples need the same shape.

## 19. The best API shape is compositional, not monolithic

The strongest pattern is:

```text
Cloudflare binding/client -> small service wrapper -> resource handle -> typed dataclass -> async stream/batch/status
```

This lets examples compose naturally:

```text
R2 object body -> ByteStream -> JsonlReader -> batches -> D1 writes -> Queue job -> AI/vector/agent event
```

What changed:

- `examples/streaming/gutenberg-stream-composition` demonstrates R2 object-body streaming, ZIP reading, byte/text/line streams, batches, checkpoints, and AI/agent/WebSocket event shapes.
- `examples/full-apps/hvsc-ai-data-search` now streams JSONL catalog data from R2 into D1 using shared streaming helpers.
- The top-level README now shows an aspirational composition snippet so readers understand the direction.

Lesson: Xampler should not become a giant SDK façade that hides Cloudflare. It should provide small Pythonic pieces that preserve platform vocabulary and compose with normal Python idioms.

## 20. Naming policy matters more than mass renaming

We saw drift between names like `QueueService`, `R2SqlClient`, `BrowserRendering`, `R2ObjectRef`, `AgentSession`, `DemoVectorIndex`, and `FakeQueueBatch`.

What changed:

- Documented the naming policy in `docs/api/unified-api-surface.md`.
- Renamed generic R2 Data Catalog `Namespace` to `CatalogNamespace`.

Lesson: suffixes should mean something:

- `*Service` for native Worker binding/action facades.
- `*Client` for REST/API-token clients.
- product nouns when the official product name is the clearest facade.
- `*Ref` for passive handles.
- `*Session` for active stateful/conversational interactions.
- `Demo*` for deterministic product stand-ins.
- `Fake*` only for tiny raw test harness objects.

## 21. Avoid compatibility baggage while the shared API is young

A strange-looking re-export appeared briefly while canonicalizing `OperationState`:

```python
from .status import OperationState as OperationState
```

That pattern can be used to signal an intentional re-export, but it made the code harder to read.

What changed:

- `OperationState` now lives only in `xampler.status`.
- `xampler.types.OperationState` is not preserved as a compatibility alias.

Lesson: Xampler's shared package is still pre-stable. It is better to keep one clear import path than preserve every transient path with compatibility shims.

## 22. Tiny local typings are a bridge, not an API

Strict pyright on every example immediately exposed missing runtime typing for `workers`, `js`, bindings, Durable Objects, and runtime-provided base classes.

What changed:

- Kept strict pyright for `xampler/`.
- Added `pyright.examples.json` for a small allowlist of stable examples.
- Added tiny `typings/workers.pyi` and `typings/js.pyi` stubs.

Lesson: the stubs are not product wrappers, compatibility layers, or official runtime definitions. They only give pyright enough shape to check selected example code. Keep them tiny, and prefer official Cloudflare/Python Workers stubs if they become sufficient.

## 23. Demo seams are acceptable only if the real path is explicit

Many Cloudflare products cannot be fully exercised by local Wrangler alone. Workers AI, Vectorize, AI Gateway, Browser Rendering, R2 SQL, R2 Data Catalog, Hyperdrive, Email Routing, Analytics Engine, Images, Queues/DLQ, Service Bindings, and deployed WebSockets all need real account resources, deployed Workers, external providers, product entitlements, or paid usage for full realism.

What changed:

- Local examples keep deterministic `/demo` routes for account-backed products.
- Added `scripts/verify_remote_examples.py` for explicitly enabled paid/remote checks.
- Added remote profiles that run real mechanisms where possible: Workers AI, Vectorize, Browser Rendering, R2 SQL, AI Gateway, and R2 Data Catalog.
- Added deployed-URL remote profiles for products that need a deployed app shape: Hyperdrive, Images, Analytics Engine, Queues/DLQ, Service Bindings, and WebSockets.

Lesson: a demo seam is fine when it is labeled, locally useful, and paired with a real route or remote verifier. It is not fine to claim the remote product ran when only deterministic Python did.

## 24. Why the skilled examples cannot all “just work for real”

The skill-shaped examples are intentionally close to Cloudflare product vocabulary, but several barriers stop them from being fully real by default:

1. **Credentials and secrets** — real AI Gateway, Browser Rendering, R2 SQL, Data Catalog, Images, and account APIs need account IDs, API tokens, gateway IDs, provider keys, or catalog tokens.
2. **Provisioned resources** — Vectorize indexes, Queues/DLQs, Hyperdrive configs, D1/R2 resources, service bindings, and Durable Object migrations must exist in the user's account.
3. **Deployed topology** — Service Bindings, Email Workers, Queue delivery/DLQ behavior, WebSocket durability, and some Hyperdrive flows need deployed Workers or multiple Workers wired together. Local single-process verification is not equivalent.
4. **Paid/product entitlements** — Browser Rendering, Workers AI, Images, Stream/media-style products, and some AI/provider calls can incur cost or require enabled account features.
5. **External systems** — Hyperdrive needs a real Postgres database; AI Gateway often needs provider credentials; Email Workers need routing configuration; Analytics needs a dataset/query path.
6. **Runtime constraints** — Python Workers run through Pyodide. Some Python libraries expect native sockets, filesystem behavior, C extensions, or long-lived processes that do not map cleanly to Workers.
7. **Local emulation gaps** — Wrangler/Miniflare does not fully emulate every account-backed product. Some bindings are explicitly “not supported” locally and can only be shape-tested or accessed remotely.

Lesson: “works for real” requires more than code. It requires credentials, resources, topology, entitlements, and sometimes deployed infrastructure. Xampler should make the path explicit, skip cleanly when prerequisites are absent, and separate local realism from remote realism.

## 25. Cloudflare examples prefer platform setup over test harness cleverness

Looking at Cloudflare's official `python-workers-examples` clarified an important pattern: their examples are small, direct, and shaped around the platform's normal workflow. They do not try to synthesize every prerequisite in application code. They use Wrangler configuration, bindings, deployment, and `.dev.vars`/secrets where appropriate.

What changed:

- Added `scripts/prepare_remote_examples.py` for explicit, env-gated remote preparation.
- Prepared Vectorize by creating the real index with Wrangler, deploying the Worker, and verifying `/describe`, `/upsert`, and `/query` against the deployed route.
- Prepared Queues/DLQ by creating both queues and deploying the producer/consumer Worker.
- Prepared Service Bindings by deploying the Python provider first and the TypeScript consumer second.
- Prepared WebSockets by deploying the Durable Object chatroom Worker and running a real two-client broadcast verifier against the deployed route.
- Prepared R2 SQL and R2 Data Catalog prerequisites by creating/enabling an R2 bucket/catalog and recording discovered state.

Lesson: prefer Cloudflare's normal control plane for prerequisites. Use Wrangler for resources and deployment, Worker bindings when a product has a Python-usable binding, and Worker secrets for runtime REST credentials.

## 26. Bindings beat REST tokens, but not every product has a Python-usable binding path

`wrangler login` is enough for many binding/resource/deploy operations because Wrangler owns the control-plane call. It is not enough when Worker code itself calls a REST API that requires a bearer token.

What changed:

- Vectorize moved from fragile `wrangler dev --remote` verification to a deployed Worker with a real Vectorize binding.
- Service Bindings and Durable Object WebSockets now verify deployed topology rather than requiring manually supplied URLs.
- Browser Rendering stayed REST-backed for now because Cloudflare's binding path is Puppeteer/Playwright-oriented and not yet ergonomic from Python Workers.
- R2 SQL and R2 Data Catalog stayed REST-backed because these examples exercise product REST APIs and token-authenticated Iceberg/R2 SQL endpoints.

Lesson: for every product, ask first: “Is there a Worker binding that Python can use directly?” If yes, prefer binding + Wrangler-managed prep. If no, keep REST credentials explicit and put them into deployed Workers with `wrangler secret put`, not committed config or ad-hoc local state.

## 27. Remote verification should have three phases: prepare, verify, cleanup

Running remote checks safely requires more structure than local smoke tests.

What changed:

- Remote preparation now requires both `XAMPLER_RUN_REMOTE=1` and `XAMPLER_PREPARE_REMOTE=1`.
- Prepared URLs and discovered identifiers are written to `.xampler-remote-state.json`, which is ignored by Git.
- Remote verification reads prepared state so users do not need to manually copy deployed URLs for prepared profiles.
- REST-backed Workers now use deployed Worker secrets instead of temporary local `.dev.vars` for remote verification.
- The HTTP verifier sends a stable User-Agent after deployed Workers returned Cloudflare `1010` bot-signature errors to default Python urllib requests.

Lesson: local verifier state and remote account state are different things. Remote examples should make lifecycle explicit: prepare resources, verify behavior, and eventually add cleanup for disposable resources.
