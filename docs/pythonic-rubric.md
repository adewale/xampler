# Pythonic Example Rubric

Last reviewed: 2026-05-01. Python anchor: **Python 3.13**.

A Pythonic example is not JavaScript translated into Python syntax. It should feel natural to an experienced Python developer while still being explicit about Cloudflare Workers, Pyodide, and the JavaScript APIs underneath.

## Credible sources

This rubric is grounded in widely used Python standards and community tools:

- The Zen of Python, PEP 20: https://peps.python.org/pep-0020/
- Style Guide for Python Code, PEP 8: https://peps.python.org/pep-0008/
- Type Hints, PEP 484: https://peps.python.org/pep-0484/
- Variable annotations, PEP 526: https://peps.python.org/pep-0526/
- Data Classes, PEP 557: https://peps.python.org/pep-0557/
- `typing` documentation for Python 3.13: https://docs.python.org/3.13/library/typing.html
- `dataclasses` documentation for Python 3.13: https://docs.python.org/3.13/library/dataclasses.html
- `asyncio` documentation for Python 3.13: https://docs.python.org/3.13/library/asyncio.html
- Python 3.13 “What’s New”: https://docs.python.org/3.13/whatsnew/3.13.html
- Ruff, a popular Python linter/formatter: https://docs.astral.sh/ruff/
- Black code style, a popular formatting guide: https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html
- pytest, a popular testing tool: https://docs.pytest.org/
- Google Python Style Guide: https://google.github.io/styleguide/pyguide.html
- The Hitchhiker’s Guide to Python: https://docs.python-guide.org/
- Real Python’s idiomatic Python material: https://realpython.com/tutorials/best-practices/
- `pathlib` documentation for path-like object APIs: https://docs.python.org/3.13/library/pathlib.html
- `contextlib` documentation for context manager patterns: https://docs.python.org/3.13/library/contextlib.html
- fsspec documentation, a common filesystem abstraction in the PyData ecosystem: https://filesystem-spec.readthedocs.io/
- s3fs documentation: https://s3fs.readthedocs.io/
- smart_open documentation: https://github.com/piskvorky/smart_open
- cloudpathlib documentation: https://cloudpathlib.drivendata.org/

## Definition

For this project, **Pythonic** means:

1. **Readable first** — source code optimizes for human comprehension. PEP 20: “Readability counts.”
2. **Explicit at important boundaries** — Cloudflare/Pyodide/JavaScript behavior is visible where it matters. PEP 20: “Explicit is better than implicit.”
3. **Simple common path** — examples present one obvious way to solve the common case before advanced escape hatches.
4. **Native Python values** — app-facing code works with `str`, `bytes`, `dict`, `list`, `None`, dataclasses, and typed objects rather than raw JS proxies.
5. **Conventional style** — `snake_case`, focused functions, clear imports, PEP 8-compatible formatting, and lint-clean code.
6. **Useful type hints** — annotations clarify public APIs without overwhelming examples with type machinery.
7. **Testable design** — interesting logic can be tested with pytest in CPython, while runtime-only behavior is isolated.
8. **Runtime honesty** — Python Workers run on Pyodide. Good examples do not pretend they are normal server-side CPython.
9. **Familiar Python metaphors** — where appropriate, examples borrow from `open()`, `pathlib`, iteration, context managers, and file-like naming without lying about object-storage or Workers semantics.
10. **Layered ergonomics** — provide a friendly path, a platform-aware path, and a documented escape hatch.

## Scoring

Score each criterion from **0 to 10**:

- **0 — Not present**: Works against Python expectations or is missing entirely.
- **1–2 — Very weak**: Mostly raw JavaScript/platform API translated into Python syntax.
- **3–4 — Weak**: Understandable, but not yet idiomatic or well layered.
- **5–6 — Adequate**: Usable Python with notable rough edges or missing teaching affordances.
- **7–8 — Strong**: Idiomatic, clear, typed where helpful, and useful for Python developers.
- **9–10 — Excellent**: Feels native to Python while teaching the Cloudflare platform accurately.

A strong example should generally average **7.5+** and have no critical criterion below **5**.

## Criteria

### 1. Clear, explicit API design

Look for small methods with intent-revealing names, keyword-only options for advanced behavior, explicit return values, and no needless cleverness.

Python grounding: PEP 20; PEP 8 naming conventions.

### 2. Native Python data shapes

Look for `dict`, `list`, `str`, `bytes`, `None`, dataclasses, and typed objects in app code. Raw `JsProxy`, JavaScript `null`, and `undefined` should be handled at the boundary.

Python grounding: PEP 557 dataclasses; Python 3.13 standard-library containers.

### 3. Pythonic naming and style

Look for `snake_case`, `CapWords` classes, constants in `UPPER_CASE`, tidy imports, and lint-clean formatting.

Python grounding: PEP 8; Ruff; Black.

### 4. Good abstraction boundaries

Look for FFI conversion localized in one layer, route code focused on HTTP behavior, storage code focused on R2 behavior, and documented escape hatches.

Python grounding: PEP 20: “Namespaces are one honking great idea”.

### 5. Type clarity without type noise

Look for useful annotations on public helpers, dataclasses for structured data, `Literal` where it communicates allowed values, and `Any` only at real JS/Python boundaries.

Python grounding: PEP 484; PEP 526; Python 3.13 `typing` docs.

### 6. Async and streaming fit the runtime

Look for consistent `async`/`await`, no blocking I/O, direct stream paths for large data, and clear separation between small buffered helpers and streaming helpers.

Python grounding: Python 3.13 `asyncio`; Cloudflare Python Workers runtime docs.

### 7. Error and missing-value behavior

Look for `None` for absence, clear 4xx responses for bad input, normalized JavaScript null/undefined, and predictable behavior for common failure modes.

Python grounding: common Python API design; Google Python Style Guide error guidance.

### 8. Readability and teachability

Look for short purposeful modules, comments that explain surprises, copy-pasteable README commands, and a simple-to-advanced progression.

Python grounding: PEP 20; Python community tutorial conventions.

### 9. Testability outside the Workers runtime

Look for fake bindings, CPython unit tests, guarded runtime imports, and no brittle top-level side effects.

Python grounding: pytest ecosystem; Python Guide testing guidance.

### 10. Honest platform fit

Look for clear notes about Pyodide, JS streams, Cloudflare binding APIs, `cfboundary` conversions, and performance-sensitive cases where data should not cross into Python.

Python grounding: practicality over purity; PEP 20: “Special cases aren't special enough to break the rules” and “Although practicality beats purity.”

### 11. Familiar Python metaphors

Look for APIs that meet Python developers where they already are: object handles, `read_text()` / `write_text()`, `read_bytes()` / `write_bytes()`, `exists()`, `stat()`, `async for`, and context managers for lifecycle-bound resources.

Good examples:

```py
obj = bucket.object("notes/hello.txt")
await obj.write_text("hello")
text = await obj.read_text()

async for item in bucket.iter_objects(prefix="logs/"):
    ...

async with await bucket.create_multipart_upload("large.bin") as upload:
    ...
```

Python grounding: built-in `open()`, `pathlib`, `contextlib`, PyData/fsspec conventions, smart_open, cloudpathlib.

### 12. Layered API ergonomics

Look for three explicit layers:

1. **Friendly path**: simple Python methods for common cases.
2. **Platform path**: Cloudflare concepts and options remain available.
3. **Escape hatch**: `.raw` or equivalent gives advanced users the underlying binding/object.

This is how examples avoid both extremes: raw translated JavaScript on one side, misleading over-abstraction on the other.

Python grounding: PEP 20's balance of simplicity, explicitness, and practicality; common design in boto3/botocore, fsspec/s3fs, smart_open, and cloudpathlib.

## Interpreting scores

| Average | Meaning |
|---:|---|
| 9.0–10.0 | Excellent Pythonic example. Feels native while teaching the platform accurately. |
| 7.5–8.9 | Strong. Good example with minor polish opportunities. |
| 5.0–7.4 | Adequate. Understandable, but still feels like translated JS or has rough edges. |
| 2.5–4.9 | Weak. Significant Python ergonomics or teaching issues. |
| 0.0–2.4 | Not Pythonic. Likely confusing for the target audience. |
