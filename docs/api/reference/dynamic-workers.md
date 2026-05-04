# Dynamic Workers

Experimental helpers live in `xampler.experimental.dynamic_workers` because Cloudflare Dynamic Workers / Worker Loader is beta-gated for deployed usage.

```python
from xampler.experimental.dynamic_workers import (
    DynamicModule,
    DynamicWorkerCode,
    DynamicWorkerLimits,
    python_fetch_worker,
    stable_worker_id,
)
```

## WorkerCode shape

```python
code = python_fetch_worker(source, compatibility_date="2026-05-01")
worker = env.LOADER.get(stable_worker_id("demo", code), lambda: code.to_raw())
response = await worker.getEntrypoint().fetch(request)
```

Use `global_outbound=None` for sandboxed examples that should not reach the Internet. Use `DynamicWorkerLimits(cpu_ms=..., subrequests=...)` when running user-edited code.

The executable examples verify Dynamic Python Workers locally. They also include the small Workers Python SDK modules in the dynamic `modules` map and keep the loader callback alive with a Pyodide proxy; those details are local-runtime glue, not a stable Xampler abstraction yet.

## Examples

- [`examples/experimental/dynamic-workers-loader/`](../../../examples/experimental/dynamic-workers-loader)
- [`examples/experimental/python-by-example-playground/`](../../../examples/experimental/python-by-example-playground)

Remote verification should remain opt-in and beta-gated until Cloudflare makes deployed Worker Loader generally available.
