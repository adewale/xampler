# Lessons Learned

Last updated: 2026-05-02.

This project is building Pythonic, executable Cloudflare examples. These are the lessons learned so far.

## 1. Runnable beats plausible

A good example is not just code that looks right. It must run under the same local workflow a user will use.

What changed:

- Added `scripts/verify_examples.py`.
- Verified `examples/start/hello-worker`, `examples/storage-data/r2-object-storage`, `examples/storage-data/kv-namespace`, `examples/start/fastapi-worker`, `examples/storage-data/d1-database`, `examples/state-events/durable-object-counter`, `examples/start/static-assets`, `examples/state-events/queues-producer-consumer`, `examples/streaming/binary-response`, `examples/network-edge/htmlrewriter-opengraph`, and `examples/state-events/cron-trigger` at different realism levels.
- Added `docs/primitive-test-realism.md` to make test depth visible.

Lesson: every new example should ship with a verifier path, even if the first verifier is shallow. If the official Cloudflare example requires local setup, our verifier should automate that setup instead of merely documenting it.

## 2. `pywrangler` is the right user-facing tool for Python examples

Plain `wrangler dev` failed for examples that depend on Python packages because dependencies such as `cfboundary` were not vendored.

What changed:

- Example package scripts now use `uv run pywrangler dev` and `uv run pywrangler deploy`.
- Docs now prefer `uv` + `pywrangler` over `npm install` + `npx wrangler`.
- Added `docs/pythonic-tooling.md`.

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
- `docs/top-10-improvement-plan.md` identifies the next action for each key primitive.

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
