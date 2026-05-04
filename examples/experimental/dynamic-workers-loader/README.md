# Dynamic Workers loader from Python Workers

This experimental example uses Cloudflare's **Dynamic Workers / Worker Loader** binding from a Python Worker.

It takes explicit inspiration from [`irvinebroque/dynamic-workers-python`](https://github.com/irvinebroque/dynamic-workers-python): a Python host Worker embeds a Python Dynamic Worker module, builds a `WorkerCode` object, and forwards a request into the child Worker. Xampler keeps that minimal one-off flow and also adds a cache-friendly `LOADER.get(id, callback)` flow for examples that repeatedly execute generated code.

It proves the shape Xampler expects for the beta API:

- the parent Worker is Python;
- the parent has a `worker_loaders` binding named `LOADER`;
- the parent loads and runs a real Dynamic Python Worker isolate locally;
- `/forward` mirrors the simple `LOADER.load(workerCode)` request-forwarding pattern from the reference repo;
- `/run` uses `LOADER.get(id, callback)` for a stable, cache-friendly worker id;
- the parent returns a `WorkerCode` object containing a Python `worker.py` module;
- `globalOutbound = null` is used as the default sandbox posture;
- the local verifier checks both execution and blocked outbound fetch behavior.

> Dynamic Workers are currently beta-gated for deployed Cloudflare usage. Wrangler/workerd local development supports the Worker Loader API. Python Dynamic Workers are supported by Cloudflare, but Cloudflare warns they start more slowly than JavaScript Dynamic Workers.

## Run locally

```bash
cd examples/experimental/dynamic-workers-loader
uv run pywrangler dev --local
```

Open <http://localhost:8787>, or verify directly:

```bash
curl http://localhost:8787/run
curl http://localhost:8787/forward
curl http://localhost:8787/blocked-network
curl http://localhost:8787/worker-code
```

## Copy this API

One-off Worker, closest to the reference repo:

```python
code = python_fetch_worker(source, compatibility_date="2026-05-01")
worker = env.LOADER.load(code.to_raw())
response = await worker.getEntrypoint().fetch(request.js_object)
```

Cache-friendly Worker for repeated generated code:

```python
from xampler.experimental.dynamic_workers import python_fetch_worker, stable_worker_id

code = python_fetch_worker(source, compatibility_date="2026-05-01")
worker = env.LOADER.get(stable_worker_id("demo", code), lambda: code.to_raw())
response = await worker.getEntrypoint().fetch("http://xampler.local/")
```

Keep this under `xampler.experimental` until Dynamic Workers are generally available and Python Worker Loader behavior is verified remotely.
