# Research: Pythonic S3 Libraries

Last reviewed: 2026-05-01. Python anchor: **Python 3.13**.

This document surveys leading open source Python libraries used with Amazon S3 or S3-compatible object storage, then extracts lessons for the Xampler R2 Python Workers API.

## Libraries surveyed

| Library | URLs | What it is |
|---|---|---|
| boto3 / botocore | https://github.com/boto/boto3, https://boto3.amazonaws.com/v1/documentation/api/latest/index.html, https://github.com/boto/botocore | Official AWS SDK for Python. botocore is the generated low-level engine; boto3 adds resources and higher-level helpers. |
| aiobotocore | https://github.com/aio-libs/aiobotocore | Asyncio wrapper around botocore. |
| aioboto3 | https://github.com/terricain/aioboto3 | Async boto3-style API built on aiobotocore. |
| s3fs | https://github.com/fsspec/s3fs, https://s3fs.readthedocs.io/ | Filesystem interface for S3 built on fsspec. |
| fsspec | https://github.com/fsspec/filesystem_spec, https://filesystem-spec.readthedocs.io/ | Common Python filesystem abstraction used by pandas, Dask, xarray, and many data tools. |
| smart_open | https://github.com/piskvorky/smart_open | Pythonic `open()`-like streaming for S3, GCS, Azure Blob, HDFS, HTTP, local files, etc. |
| minio-py | https://github.com/minio/minio-py, https://min.io/docs/minio/linux/developers/python/API.html | Python client for MinIO and S3-compatible object storage. |
| django-storages | https://github.com/jschneier/django-storages, https://django-storages.readthedocs.io/ | Django storage backend for S3 and other object stores. |
| cloudpathlib | https://github.com/drivendataorg/cloudpathlib, https://cloudpathlib.drivendata.org/ | `pathlib`-style paths for cloud object storage including S3. |
| moto | https://github.com/getmoto/moto, https://docs.getmoto.org/ | AWS service mocks for tests, including S3. Not a production S3 client, but important for Pythonic testing patterns. |

## Pythonic assessment

Scores use the project rubric in [`docs/pythonic-rubric.md`](pythonic-rubric.md).

| Library | Pythonic score | Strengths | Tradeoffs |
|---|---:|---|---|
| boto3 | 6.75 / 10 | Stable, comprehensive, familiar; exposes resources, paginators, waiters, transfer helpers. | Service-shaped API, many dictionaries, CamelCase AWS parameters, `ClientError` parsing, mixed client/resource abstractions. |
| botocore | 5.0 / 10 | Precise low-level generated API; strong configuration/retry machinery. | Not intended to feel Pythonic; mirrors AWS service models. |
| aiobotocore | 6.5 / 10 | Brings botocore to asyncio; close to underlying AWS docs. | Async but still botocore-shaped; context management is good but ergonomics remain low-level. |
| aioboto3 | 7.5 / 10 | Familiar boto3 surface with async context managers; good fit for async apps. | Inherits boto3’s service-shaped API and dictionaries. |
| s3fs / fsspec | 9.0 / 10 | Excellent Pythonic abstraction: file-like API, URLs, globbing, filesystem semantics, integrations with pandas/Dask. | Filesystem metaphor can hide object-store semantics; not ideal for every R2 feature like metadata or conditionals. |
| smart_open | 9.25 / 10 | Very Pythonic: `open()` mental model, streaming, compression support, simple common path. | Intentionally narrow; not a full object-storage management API. |
| minio-py | 7.75 / 10 | Clear explicit object-store client, typed-ish result objects, S3-compatible without AWS heaviness. | Java-inspired method names in places; still object-store/API shaped. |
| django-storages | 8.5 / 10 | Fits Django’s `Storage` interface; users rarely touch S3 details. | Pythonic only inside Django; hides platform details and exposes fewer advanced S3/R2 features. |
| cloudpathlib | 9.5 / 10 | Strongly Pythonic: `pathlib`-like paths, intuitive operations, local caching, nice ergonomics. | Path abstraction can imply folders/files more strongly than object storage actually supports. |
| moto | 8.75 / 10 | Great developer ergonomics for tests; decorators/context managers make AWS tests feel local. | Mock fidelity can lag real services; not a runtime API. |

## What these libraries know about being Pythonic

### 1. Offer a familiar Python metaphor

The most Pythonic libraries do not start from the cloud API. They start from a Python concept:

- `smart_open.open("s3://bucket/key")` borrows Python’s built-in `open()`.
- `cloudpathlib.S3Path("s3://bucket/key")` borrows `pathlib.Path`.
- `s3fs.S3FileSystem` borrows filesystem operations.
- `django-storages` borrows Django’s `Storage` interface.

**Lesson for us:** `R2Bucket` is good, but we can add optional Python-native metaphors:

```py
obj = bucket.object("notes/hello.txt")
await obj.write_text("hello")
text = await obj.read_text()
```

or:

```py
async with bucket.open("logs/app.txt", "wb") as f:
    await f.write(chunk)
```

We should be careful: Workers streams are not normal CPython file objects. But a small object handle could improve ergonomics.

### 2. Use context managers for resource lifecycles

`aioboto3`, `aiobotocore`, `smart_open`, `s3fs`, and `moto` all benefit from context managers.

Patterns:

```py
async with session.client("s3") as s3:
    ...

with smart_open.open("s3://bucket/key") as f:
    ...

@mock_aws
async def test_something():
    ...
```

**Lesson for us:** Multipart upload is a resource lifecycle and should support `async with`. We added this. We can go further with test helpers and maybe object-level streaming helpers.

### 3. Separate common path from advanced path

`smart_open` is loved because it makes the common case tiny. boto3 remains comprehensive by exposing advanced service details separately.

**Lesson for us:** Keep both:

```py
await bucket.put_text("hello.txt", "hello")
```

and:

```py
await bucket.put(
    "hello.txt",
    body,
    http_metadata=R2HttpMetadata(cache_control="public, max-age=3600"),
    only_if=R2Conditional(etag_does_not_match="abc"),
)
```

The simple path should never require users to understand `to_js`, `JsProxy`, `ReadableStream`, or R2 options.

### 4. Model results, not just dictionaries

boto3 returns many dictionaries because it maps generated service APIs. More Pythonic libraries return objects or file/path abstractions.

**Lesson for us:** Our dataclasses are the right direction. Keep returning:

- `R2ObjectInfo`
- `R2ListResult`
- `R2UploadedPart`
- `R2HttpMetadata`

instead of raw dictionaries.

### 5. Provide iteration abstractions

Python developers expect iteration:

- `for path in fs.glob(...)`
- paginators in boto3
- `Path.iterdir()` in pathlib/cloudpathlib

**Lesson for us:** `iter_objects()` is more Pythonic than manual cursor handling:

```py
async for obj in bucket.iter_objects(prefix="logs/"):
    print(obj.key, obj.size)
```

Manual `list(cursor=...)` should remain available.

### 6. Make tests feel local

`moto` is popular because cloud tests become normal Python tests.

**Lesson for us:** our fakes should become a first-class testing module for examples:

```py
from examples.testing import FakeR2Bucket
```

Then examples can show both Worker runtime code and CPython tests.

### 7. Do not overfit to one backend unless that is the point

fsspec, smart_open, cloudpathlib, and django-storages succeed partly because they abstract multiple storage backends.

**Lesson for us:** Our goal is Cloudflare Developer Platform education, so R2-specific concepts should remain visible. But the API can still feel portable where Python developers expect it: `read_text`, `write_bytes`, `iter_objects`, metadata dataclasses.

### 8. Preserve escape hatches

boto3/botocore are popular because advanced users can reach the exact service feature. s3fs and smart_open expose `client_kwargs`, `transport_params`, or similar.

**Lesson for us:** Keep `.raw` on wrappers. It is not an impurity; it is an honest escape hatch for JavaScript-native streams and features we have not wrapped.

## Where our API is already competitive

- We use dataclasses where boto3 often returns dictionaries.
- We provide small helpers for text/bytes instead of forcing a service-shaped API.
- We expose async streaming explicitly, which fits Workers better than pretending R2 is a local file.
- We isolate FFI conversion, which none of the normal S3 libraries need to solve.
- We now support `async with` for multipart upload lifecycle safety.

## Where we should improve

### Add an object-handle API

A more Pythonic layer could look like:

```py
note = bucket.object("notes/hello.txt")
await note.write_text("hello")
assert await note.read_text() == "hello"
info = await note.stat()
await note.delete()
```

This borrows from `pathlib` and file APIs without pretending R2 has real directories.

### Add `exists()`

Python users often expect this:

```py
if await bucket.exists("notes/hello.txt"):
    ...
```

It would be a thin wrapper over `head()`.

### Add `read_*` / `write_*` aliases

`put_*` and `get_*` match object-store vocabulary. `read_*` and `write_*` match Python file vocabulary.

Possible compromise:

```py
await bucket.write_text(key, text)  # alias for put_text
text = await bucket.read_text(key)  # alias for get_text
```

### Add a testing fake as a supported artifact

Promote the current test fake into reusable example infrastructure.

### Add richer error types

Instead of letting every runtime error leak through, define a small exception hierarchy for validation errors in our wrapper:

```py
class R2Error(Exception): ...
class R2MultipartError(R2Error): ...
class R2ValidationError(ValueError, R2Error): ...
```

Be careful not to hide Cloudflare errors too aggressively.

## Bottom line

The most Pythonic S3 libraries win by meeting Python developers where they already are: `open()`, `pathlib`, iteration, context managers, dataclasses/objects, and local tests.

Our current API is Pythonic for a Workers-first R2 wrapper, but we can learn three big things:

1. Add a small object-handle API inspired by `pathlib`/`cloudpathlib`.
2. Add read/write aliases and `exists()` for common Python expectations.
3. Promote fakes/testing helpers so examples feel runnable with normal Python tools.
