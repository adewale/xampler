# Dynamic Workers loader from Python Workers

This experimental example uses Cloudflare's **Dynamic Workers / Worker Loader** binding from a Python Worker.

It proves the shape Xampler expects for the beta API:

- the parent Worker is Python;
- the parent has a `worker_loaders` binding named `LOADER`;
- the parent loads a real Dynamic Worker isolate locally;
- the parent exposes a `WorkerCode` object containing a Python `worker.py` module at `/worker-code`;
- `globalOutbound = null` is used as the default sandbox posture.

> Dynamic Workers are currently beta-gated for deployed Cloudflare usage. Wrangler/workerd local development supports the Worker Loader API. This example verifies the loader with a JavaScript child isolate because that path is reliable locally from a Python parent. `/worker-code` documents the Dynamic Python WorkerCode shape Cloudflare exposes; keep deployed Dynamic Python verification beta-gated.

## Run locally

```bash
cd examples/experimental/dynamic-workers-loader
uv run pywrangler dev --local
```

Open <http://localhost:8787>, or verify directly:

```bash
curl http://localhost:8787/run
curl http://localhost:8787/blocked-network
curl http://localhost:8787/worker-code
```

## Copy this API

```python
from xampler.experimental.dynamic_workers import python_fetch_worker, stable_worker_id

code = python_fetch_worker(source, compatibility_date="2026-05-01")
worker = env.LOADER.get(stable_worker_id("demo", code), lambda: code.to_raw())
response = await worker.getEntrypoint().fetch("http://xampler.local/")
```

Keep this under `xampler.experimental` until Dynamic Workers are generally available and Python Worker Loader behavior is verified remotely.
