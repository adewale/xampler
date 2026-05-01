# Comparison: Our R2 Python Workers Example vs AWS S3 Python Examples

Last reviewed: 2026-05-01. Python anchor: **Python 3.13**.

AWS/Amazon sources considered:

- AWS SDK for Python (Boto3) S3 examples: https://docs.aws.amazon.com/code-library/latest/ug/python_3_s3_code_examples.html
- Boto3 S3 service resource docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
- Boto3 S3 client docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/index.html
- Boto3 S3 transfer docs: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3.html
- S3 presigned URL docs: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
- AWS SDK code examples repository: https://github.com/awsdocs/aws-doc-sdk-examples

## High-level contrast

AWS S3 examples are comprehensive because S3 is mature, large, and supported by boto3 directly in normal CPython. They cover many operations across buckets, objects, access control, encryption, multipart transfer, presigned URLs, batch actions, and higher-level scenarios.

Our R2 example has a different job: teach Python developers how to use a JavaScript-first Cloudflare binding from Python Workers. The hard part is not just object storage. The hard part is crossing the Pyodide/JavaScript boundary in a way that still feels like Python.

## Where AWS is stronger

| Area | AWS strength |
|---|---|
| Breadth | AWS examples cover a very large S3 surface area: bucket creation/deletion, object CRUD, copy, versioning, lifecycle, encryption, ACLs/policies, presigned URLs, multipart transfer, and more. |
| Mature SDK ergonomics | boto3 is a Python SDK. The examples do not need to explain JS/Python FFI, `JsProxy`, or Web Streams. |
| Production scenarios | AWS has scenario-based examples that combine multiple operations into workflows. |
| Transfer helpers | boto3’s transfer manager (`upload_file`, `download_file`, multipart handling) provides high-level Python APIs that are already familiar to Python developers. |
| Client-side scripts | AWS examples often include local CPython scripts, which are easy to run and test outside a cloud runtime. |

## Where AWS examples are less Pythonic

This is not a criticism of boto3 itself; it is a consequence of documenting a huge generated SDK.

| Area | Issue |
|---|---|
| API shape | Many examples expose AWS’s wire/API vocabulary directly: `Bucket`, `Key`, `Body`, `ContentType`, `Metadata`, `ExtraArgs`. That is accurate, but not always idiomatic Python. |
| Error handling | Examples often require readers to learn `botocore.exceptions.ClientError` and inspect response codes. Useful, but verbose for beginners. |
| Generated clients | `client` calls return large dictionaries. This is practical, but less expressive than small dataclasses for tutorial-facing code. |
| Mixed abstraction levels | Some AWS examples jump between low-level clients, higher-level resources, waiters, paginators, and transfer managers. That breadth can obscure the beginner path. |
| Style variability | The code library spans many contributors and years. Some examples are excellent; others are more service-API-shaped than Python-shaped. |

## Where we beat AWS for this audience

| Area | Our advantage |
|---|---|
| Pythonic façade | `R2Bucket`, `R2ObjectInfo`, `R2ListResult`, `R2Range`, and `R2Conditional` provide focused, typed, Python-facing concepts. |
| Boundary clarity | We explicitly show where `cfboundary` converts Python values to JS values and JS values back to Python. AWS examples do not need this, but Python Workers users do. |
| Small-to-large progression | The example starts with `put_text()`/`get_text()`, then bytes, then metadata, range reads, conditionals, streaming, and multipart. |
| Streaming honesty | We show when to keep data on the JavaScript stream path instead of copying it into Python memory. |
| Testability | The wrapper is tested with CPython fake bindings, so the core API can evolve safely outside Workers. |
| Modern Python | The examples use Python 3.13-era style: dataclasses, `Literal`, union syntax, keyword-only dataclasses, and Ruff-clean formatting. |

## Where we should learn from AWS

| AWS pattern | How to apply it here |
|---|---|
| Scenario examples | Add complete workflows: browser upload, image/file gallery, backup/restore, and event-driven processing. |
| Presigned URL coverage | Add an R2 S3-compatible boto3 example for presigned GET/PUT URLs. |
| Transfer tooling | Provide a local Python uploader script for multipart uploads, similar to Cloudflare’s multipart guide and boto3 transfer examples. |
| Paginators | Add a Pythonic async iterator for R2 listing so users can write `async for obj in bucket.iter_objects(prefix=...)`. |
| Error recipes | Add common R2 errors and recovery patterns: missing upload ID, failed multipart completion, checksum mismatch, bad range, and permission issues. |
| Separate beginner and advanced paths | Keep the beginner README short, and move exhaustive API coverage into reference docs. |

## Thoroughness score

| Project | Score | Notes |
|---|---:|---|
| AWS S3 Python examples | 10 / 10.0 for breadth | Very comprehensive across S3. Less focused as a teaching path for one coherent Pythonic abstraction. |
| `r2-01` current example | 8.0 / 10.0 for breadth | Strong Worker-binding coverage. Still needs separate examples for S3-compatible API, presigned URLs, CORS/browser upload, notifications, lifecycle, and public buckets. |

## Pythonic score

| Project | Score | Notes |
|---|---:|---|
| AWS S3 Python examples | 7.0 / 10.0 | Mature and practical, but often mirrors service API shape and generated boto3 dictionaries. Some examples are very good, but the collection is uneven. |
| `r2-01` current example | 8.25 / 10.0 | More deliberately Pythonic for the target audience, especially with dataclasses and helper methods. Needs more route tests and richer error recipes. |

## Bottom line

AWS wins on maturity and surface-area coverage. We can win on teaching quality for Python Workers by being explicit about the runtime boundary, offering a small Pythonic façade, and separating simple examples from advanced platform features.
