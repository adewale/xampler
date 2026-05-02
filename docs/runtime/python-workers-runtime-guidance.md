# Python Workers Runtime Guidance

Last reviewed: 2026-05-02.

This captures the Python Workers guidance we apply in Xampler after reviewing the current `python-workers-skill` PRs.

## Type checking and tiny local stubs

The main strict pyright target is the shared `xampler/` package. A second profile, `pyright.examples.json`, checks a small allowlist of stable examples without trying to type the entire Workers runtime surface.

The `typings/` directory contains intentionally tiny `.pyi` stubs for modules that exist in the Python Workers runtime, such as `workers` and `js`. They provide just enough shape for pyright to understand selected examples:

- `Response` and `Response.json(...)`
- `WorkerEntrypoint`, `WorkflowEntrypoint`, and `DurableObject` base classes
- a minimal `js.fetch(...)`

These stubs are not product wrappers, not compatibility shims, and not a substitute for official runtime types. Keep them minimal; if official Python Workers type stubs become sufficient, prefer those and delete the local stubs.

## PR coverage note

I inspected the pull-request refs available from Git for `adewale/python-workers-skill`, including PR heads `1`, `2`, and `3`. That covers both merged/closed work that is now on `main` and the still-open PR heads exposed under `refs/pull/*/head`. The actionable changes for Xampler came mainly from PRs 2 and 3.

## Sync and async HTTP

Xampler's position is:

- Prefer `workers.fetch()`, `js.fetch`, or async HTTP clients for Worker request paths.
- Do **not** claim synchronous HTTP libraries categorically cannot work.
- Avoid sync/blocking calls in hot paths because Workers are request/CPU constrained and Python Workers pay extra Pyodide overhead.
- For examples, use platform-native `fetch` when calling Cloudflare REST APIs because it avoids socket/runtime ambiguity and mirrors Workers documentation.

In short: **async/fetch is the recommended Worker style; sync HTTP is not our default teaching path, but we should not document it as impossible unless a specific library is known to fail.**

## Python snapshots

Python Workers run CPython through Pyodide in a V8 isolate. Cloudflare can snapshot initialized WebAssembly memory so imports and module initialization do not have to be repeated from scratch for every cold start.

What this means for Xampler:

- Heavy examples should use `python_dedicated_snapshot` when practical.
- Module-level constants and imports are good snapshot candidates.
- Module-level entropy is bad: avoid `random`, `secrets`, `uuid.uuid4()`, or `os.urandom()` during import time.
- Snapshotting improves cold start, but Python still has more CPU/cold-start cost than JavaScript Workers.

## Large binary guidance

There are two different use cases:

1. **Process bytes in Python** — OK for bounded chunks, thumbnails, signatures, hashes, JSONL lines, small binary fixtures.
2. **Serve or proxy large binary objects** — do not round-trip JS `ReadableStream` → Python `bytes` → JS response.

For large files, prefer passing the JavaScript stream directly to a JavaScript `Response`, or let R2/static assets serve the file without waking Python. Xampler's Gutenberg and HVSC files are golden files for movement/streaming examples, not an invitation to load 80 MiB into Python memory.

## CPU limits for heavy examples

Python Workers consume more CPU than equivalent JavaScript Workers. Examples that parse archives, stream many records, run AI/agent orchestration, or initialize larger Python packages should document and often configure `limits.cpu_ms`.

Xampler currently treats these as heavy examples:

- `examples/full-apps/hvsc-ai-data-search`
- `examples/streaming/gutenberg-stream-composition`
- `examples/ai-agents/langchain-style-chain`
- `examples/ai-agents/agents-sdk-tools`
- `examples/start/fastapi-worker`

## `to_py` guidance

Native Pyodide `to_py` is a **method on `JsProxy` objects**, not a function to import from `pyodide.ffi`.

Xampler examples may still use:

```python
from cfboundary.ffi import to_py
```

That is deliberate: `cfboundary.to_py()` is our wrapper abstraction around safe conversion. Docs should distinguish:

- native Pyodide: `js_proxy.to_py()`;
- Xampler/cfboundary abstraction: `to_py(js_proxy)`.

## Direct `to_js` dictionary conversion audit

Xampler should use `cfboundary.ffi.to_js()` for dictionaries rather than raw `pyodide.ffi.to_js()` so dicts become JavaScript objects, not Maps.

Current audit result: direct `to_js({...})` calls in examples import `to_js` from `cfboundary.ffi`, not `pyodide.ffi`, so they are acceptable. Keep this rule for future examples.
