# Python by Example Playground

A Cloudflare Python Workers playground for [`pycollege/python-by-example`](https://github.com/pycollege/python-by-example), inspired by [Go by Example](https://gobyexample.com/).

Every vendored Python source example gets a page with:

- the original title and summary;
- links back to the upstream lesson/source file;
- an editable code textarea;
- a **Run Python** button;
- execution inside a Dynamic Python Worker isolate.

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

The parent Worker is Python. When you press **Run Python**, it creates a Dynamic Python Worker module that embeds the edited code, captures `stdout`/`stderr`, and returns JSON.

The Dynamic Worker is configured with:

- `globalOutbound = null` so examples cannot use network access by default;
- small CPU/subrequest limits;
- an ID derived from the generated code for cache-friendly reloads.

This requires the Dynamic Workers / Worker Loader binding:

```jsonc
{
  "worker_loaders": [{ "binding": "LOADER" }]
}
```

Remote deployment is beta-gated by Cloudflare. Keep this example experimental until deployed Python Dynamic Workers are broadly available and remotely verified.
