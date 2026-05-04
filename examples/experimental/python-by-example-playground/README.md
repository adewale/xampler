# Python by Example Playground

A Cloudflare Python Workers playground for [`pycollege/python-by-example`](https://github.com/pycollege/python-by-example), inspired by [Go by Example](https://gobyexample.com/) and the Python host/child Dynamic Worker shape from [`irvinebroque/dynamic-workers-python`](https://github.com/irvinebroque/dynamic-workers-python).

Every vendored Python source example gets a page with:

- the original title and summary;
- links back to the upstream lesson/source file;
- an editable code textarea;
- a **Run Python** button;
- execution inside a Dynamic Python Worker isolate.

The index deliberately uses a learning order rather than alphabetical order: basics, control flow, collections, functions/classes, files/JSON/time, async, and networking. Examples that require process-level CLI/test-runner/server behavior are grouped under **Unsupported in this playground**.

## Python runtime version

The local Cloudflare Python Workers toolchain currently installs a Pyodide/Python 3.13 runtime for Workers. This playground therefore targets Python 3.13 behavior. Python 3.14 support should be added when Cloudflare's Python Workers runtime and `pywrangler` toolchain expose a Python 3.14/Pyodide build; until then, advertising 3.14 would be misleading.

## Attribution

This example vendors educational code from:

- Repository: <https://github.com/pycollege/python-by-example>
- Project: Python by Example
- Author/copyright line from upstream license: Dariush Abbasi (<https://github.com/dariubs>)
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)

The Xampler additions are the Cloudflare Worker, Dynamic Worker runner, and playground UI. Upstream lesson/source links are preserved on each page.

## Refresh upstream examples

```bash
uv run python scripts/fetch_python_by_example.py
```

The script reads `source/*.py`, pairs each file with `lessons/*.md` where available, and rewrites `src/examples_data.py` with attribution metadata.

## Run locally

```bash
cd examples/experimental/python-by-example-playground
uv run pywrangler dev --local
```

Open <http://localhost:8787>.

## How execution works

The parent Worker is Python. When you press **Run Python**, it creates a Dynamic Python Worker module that embeds the edited code, captures `stdout`/`stderr`, and returns JSON. Like the reference repo, the child Worker source is assembled as Python source in the host and passed to the Worker Loader as a `WorkerCode` object. Unlike the minimal reference, the playground uses `LOADER.get(id, callback)` instead of one-off `LOADER.load(...)` so edited snippets get stable cache-friendly worker ids.

The Dynamic Worker is configured with:

- `globalOutbound = null` so examples cannot use network access by default;
- small CPU/subrequest limits;
- an ID derived from the generated code for cache-friendly reloads;
- an optional Outbound Worker gateway for the HTTP Client example.

This requires the Dynamic Workers / Worker Loader binding:

```jsonc
{
  "worker_loaders": [{ "binding": "LOADER" }]
}
```

Remote deployment is beta-gated by Cloudflare. Keep this example experimental until deployed Python Dynamic Workers are broadly available and remotely verified.
