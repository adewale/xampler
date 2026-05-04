# Python by Example Playground

A Cloudflare Python Workers playground for [`pycollege/python-by-example`](https://github.com/pycollege/python-by-example), inspired by [Go by Example](https://gobyexample.com/).

Every vendored Python source example gets a page with:

- the original title and summary;
- links back to the upstream lesson/source file;
- an editable code textarea;
- a **Run Python** button;
- immediate execution in the Python Worker runtime.

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

The Worker is Python. When you press **Run Python**, the route captures `stdout`/`stderr`, executes the edited snippet with `exec()`, and returns JSON.

This is intentionally an educational playground, not a production sandbox for untrusted users. The companion [`dynamic-workers-loader`](../dynamic-workers-loader) example demonstrates Worker Loader isolation. Cloudflare documents Python modules for Dynamic Workers, but local Dynamic Python Workers currently need extra runtime care, so this playground keeps execution simple and verifiable.
