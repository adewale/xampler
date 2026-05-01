# Pythonic Assessment: `r2-01`

This assesses the current R2 example against [`docs/pythonic-rubric.md`](pythonic-rubric.md).

Last reviewed: 2026-05-01. Python anchor: **Python 3.13**.

## Summary

Current Pythonic score: **3.3 / 4.0**
Current R2 feature thoroughness score: **3.2 / 4.0**

The example is strongly Pythonic in its core design: it introduces a small `R2Bucket` façade, uses dataclasses for Python-native metadata and options, normalizes missing JavaScript values to `None`, separates small-object helpers from streaming paths, and keeps most `cfboundary` usage inside the boundary layer.

It now covers most key Workers-binding R2 operations: put/get/head/delete/list, metadata, custom metadata, checksums, storage class, range reads, conditionals, batch delete, streaming, and multipart upload. Product-level features such as CORS, public buckets, lifecycle rules, event notifications, and S3-compatible presigned URLs should become separate examples rather than overloading this first Worker.

## Scores

| Criterion | Score | Assessment |
|---|---:|---|
| Clear, explicit API design | 3 | `put_text()`, `get_text()`, `put_bytes()`, `get_bytes()`, `put_stream()`, `R2Range`, and `R2Conditional` are clear. The route file is now broad because it demonstrates many features, so the simple path needs to remain prominent in docs. |
| Native Python data shapes | 4 | Metadata and option concepts are dataclasses. Missing objects become `None`. Lists become Python lists. Text and bytes helpers return `str` and `bytes`. Multipart parts are modeled as `R2UploadedPart`. |
| Pythonic naming and style | 4 | Names are idiomatic `snake_case`; classes use `CapWords`; constants use type aliases; Ruff passes. |
| Good abstraction boundaries | 3 | `r2_pythonic.py` owns most R2/FFI conversion work, while `entry.py` owns HTTP routes. The intentional `raw` escape hatch is documented. Response construction is still repeated in the example and should become shared infrastructure later. |
| Type clarity without type noise | 3 | `Literal`, dataclasses, and explicit return types help. `Any` remains visible at Worker/JS boundaries, which is appropriate but noisy in `entry.py`. |
| Async and streaming fit the runtime | 4 | The example cleanly distinguishes small buffered helpers from direct streaming upload/download and multipart upload. It avoids blocking I/O. |
| Error and missing-value behavior | 3 | Missing R2 objects become `None` and routes return 404. Bad `limit` values produce 400. More multipart and range validation would improve this. |
| Readability and teachability | 3 | README and docs need to keep the simple path first because the route file now demonstrates many R2 features. Feature coverage is documented separately to avoid overwhelming beginners. |
| Testability outside Workers | 3 | `r2_pythonic.py` is tested in CPython with a fake R2 binding. Route tests and multipart fake tests are still needed. |
| Honest platform fit | 3 | Docs and code mention `cfboundary`, `JsProxy`, `Uint8Array`, raw JS streams, and when to keep data out of Python memory. The wrapper avoids hiding the platform completely. |

## What is most Pythonic already

- **Dataclasses for R2 metadata and options**: `R2ObjectInfo`, `R2ListResult`, `R2Range`, `R2Conditional`, and `R2UploadedPart` are Python-facing objects over JS API shapes.
- **Common-path helpers**: `put_text()`, `get_text()`, `put_bytes()`, and `get_bytes()` match what Python developers expect from storage APIs.
- **Boundary localization**: `to_js()`, `to_js_bytes()`, `to_py()`, and `is_js_missing()` are mostly contained in `r2_pythonic.py`.
- **`None` for absence**: `get()`, `head()`, and failed conditional `put()` return `None`.
- **Streaming honesty**: `put_stream()`, `/objects/<key>/stream`, and multipart upload avoid pretending large R2 data should be copied through Python memory.

## Improvement backlog

1. Add route tests for `entry.py` with fake request/response objects.
2. Add fake multipart tests for `create_multipart_upload`, `upload_part`, `complete`, and `abort`.
3. Add an async iterator helper for paginated list results: `async for obj in bucket.iter_objects(...)`.
4. Add richer validation for range values and multipart request bodies.
5. Split future product-level R2 features into separate examples: presigned URLs, browser uploads with CORS, event notifications, lifecycle rules, public buckets.
6. Consider a shared response helper module for future examples so each example does not repeat `js.Response.new(..., to_js(...))` boilerplate.

## Overall judgment

`r2-01` is now a strong foundation for the rest of the examples. It is Pythonic where it matters most: user-facing storage operations, metadata modeling, missing-value behavior, async streaming, and testability. Its main risk is breadth: a comprehensive R2 sample can overwhelm beginners unless the documentation preserves the progression from simple to advanced.
