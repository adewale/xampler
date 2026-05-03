# 01 — R2 from Python Workers

This example demonstrates [Cloudflare R2](https://developers.cloudflare.com/r2/) from a Python Worker with the shared `xampler.r2` wrapper around the JavaScript binding.

It teaches R2 in layers:

1. **Simple small-object helpers** — `put_text()`, `get_text()`, `put_bytes()`, `get_bytes()`.
2. **Metadata and controls** — custom metadata, HTTP metadata, checksums, storage class, range reads, ETag conditionals, listing, and deletes.
3. **Streaming and multipart** — large uploads/downloads without copying data through Python memory.

The stable wrapper now lives in `xampler.r2`:

```py
from xampler.r2 import R2Bucket, R2HttpMetadata, R2Range
```

The old example-local `src/r2_pythonic.py` module has been removed; new code should import from `xampler.r2`.

The wrapper uses [`cfboundary`](https://github.com/adewale/cfboundary) for low-level conversions:

- `to_js()` for JavaScript options objects.
- `to_js_bytes()` for Python `bytes` -> JavaScript `Uint8Array`.
- `to_py()` for metadata/list results.
- `is_js_missing()` for JavaScript `null`/`undefined`.
- `stream_r2_body()` and `consume_readable_stream()` for body conversion when you intentionally need Python bytes.

## The simple Pythonic path

Most Python developers should start here:

```py
bucket = R2Bucket(self.env.BUCKET)

note = bucket.object("notes/hello.txt")
await note.write_text("Hello from Python Workers + R2")
text = await note.read_text()

await bucket.write_bytes("images/logo.bin", b"...")
body = await bucket.read_bytes("images/logo.bin")
```

For large objects, prefer the streaming path:

```py
await bucket.put_stream("uploads/big-file", request.body)
obj = await bucket.get("uploads/big-file")
return Response(obj.raw.body)
```

`obj.raw` is intentional: it keeps JavaScript-native streams on the JavaScript side for performance.

## API surface

### Friendly object-handle API

```py
obj = bucket.object("notes/hello.txt")

await obj.write_text("hello")
text = await obj.read_text()

await obj.write_bytes(b"hello")
body = await obj.read_bytes()

exists = await obj.exists()
info = await obj.stat()
await obj.delete()
```

### Bucket-level convenience methods

```py
await bucket.write_text("notes/hello.txt", "hello")
text = await bucket.read_text("notes/hello.txt")

await bucket.write_bytes("blob.bin", b"bytes")
body = await bucket.read_bytes("blob.bin")

exists = await bucket.exists("blob.bin")
```

### Platform-aware R2 API

```py
await bucket.put_text("notes/hello.txt", "hello")
await bucket.put_bytes("blob.bin", b"bytes")
await bucket.put_stream("upload.bin", request.body)

obj = await bucket.get("upload.bin")
info = await bucket.head("upload.bin")
page = await bucket.list(prefix="logs/", delimiter="/", include=["customMetadata"])

async for info in bucket.iter_objects(prefix="logs/"):
    print(info.key, info.size)
```

### Advanced options and lifecycle APIs

```py
await bucket.put_bytes(
    "archive/report.pdf",
    data,
    http_metadata=R2HttpMetadata(
        content_type="application/pdf",
        cache_control="public, max-age=3600",
    ),
    custom_metadata={"source": "example"},
    checksum=("sha256", digest),
    storage_class="InfrequentAccess",
)

part = R2Range(offset=0, length=1024)
first_kb = await bucket.read_bytes("archive/report.pdf", byte_range=part)

async with await bucket.create_multipart_upload("large.bin") as upload:
    uploaded = await upload.upload_part(1, request.body)
    await upload.complete([uploaded])
```

The API has three layers: a friendly Python object-handle layer, an R2 vocabulary layer, and the `.raw` escape hatch for native Workers streams and unsupported JavaScript APIs.

## Setup

Create an R2 bucket once:

```bash
npx wrangler@latest r2 bucket create xampler-r2-demo
```

Run locally with Python tooling:

```bash
cd examples/storage-data/r2-object-storage
uv run pywrangler dev
```

You do not need to run `npm install` for this Python example. `pywrangler` invokes Wrangler for you.

By default, Wrangler local development uses local R2 storage. Use a remote binding if you intentionally want local development to operate on a real bucket.

## Try the simple API

```bash
curl -X PUT 'http://localhost:8787/simple/hello.txt' \
  -H 'content-type: text/plain' \
  --data 'Hello from Python Workers + R2'

curl 'http://localhost:8787/simple/hello.txt'
```

## Upload and download the included JPEG fixture

This example includes `fixtures/BreakingThe35.jpeg` so the first R2 example demonstrates a real binary file upload/download, not just strings.

```bash
curl -X PUT 'http://localhost:8787/objects/images/BreakingThe35.jpeg' \
  -H 'content-type: image/jpeg' \
  --data-binary @fixtures/BreakingThe35.jpeg

curl 'http://localhost:8787/objects/images/BreakingThe35.jpeg/stream' \
  -o /tmp/BreakingThe35-from-r2.jpeg

cmp fixtures/BreakingThe35.jpeg /tmp/BreakingThe35-from-r2.jpeg
```

If `cmp` prints nothing, the downloaded file matches the uploaded fixture exactly.

## Try metadata, checksum, and storage class

```bash
curl -X PUT 'http://localhost:8787/advanced/report.bin?ia=1' \
  -H 'content-type: application/octet-stream' \
  --data-binary 'important bytes'

curl 'http://localhost:8787/objects/report.bin'
```

This route calculates SHA-256 in Python, passes it to R2 as a checksum, stores custom metadata, and optionally uses the `InfrequentAccess` storage class.

## Try range reads

```bash
curl -X PUT 'http://localhost:8787/bytes/range.txt' --data 'abcdefghijklmnopqrstuvwxyz'
curl 'http://localhost:8787/range/range.txt?offset=5&length=10'
curl 'http://localhost:8787/range/range.txt?suffix=6'
```

## Try listing

```bash
curl 'http://localhost:8787/list?prefix=notes/&limit=100'
curl 'http://localhost:8787/list?delimiter=/'
curl 'http://localhost:8787/list?include=httpMetadata,customMetadata'
```

Use the returned `cursor` with `?cursor=...` when `truncated` is true.

## Try streaming upload/download

`/objects/<key>` stores the request body stream directly in R2. `/objects/<key>/stream` returns the R2 body stream directly to the client.

```bash
python3 - <<'PY' > /tmp/r2-large.txt
for i in range(100_000):
    print(f"line {i}")
PY

curl -X PUT 'http://localhost:8787/objects/large.txt' \
  -H 'content-type: text/plain' \
  --data-binary @/tmp/r2-large.txt

curl 'http://localhost:8787/objects/large.txt/stream' -o /tmp/r2-large-out.txt
cmp /tmp/r2-large.txt /tmp/r2-large-out.txt
```

## Try multipart upload

Multipart upload is for large objects and clients that can keep track of `upload_id`, part numbers, and part ETags.

```bash
curl -X POST 'http://localhost:8787/multipart/big.bin?action=create'

# Suppose the response contains {"upload_id":"abc"}.
curl -X PUT 'http://localhost:8787/multipart/big.bin?action=upload-part&upload_id=abc&part_number=1' \
  --data-binary @part-1.bin

curl -X PUT 'http://localhost:8787/multipart/big.bin?action=upload-part&upload_id=abc&part_number=2' \
  --data-binary @part-2.bin

curl -X POST 'http://localhost:8787/multipart/big.bin?action=complete&upload_id=abc' \
  -H 'content-type: application/json' \
  --data '{"parts":[{"part_number":1,"etag":"..."},{"part_number":2,"etag":"..."}]}'
```

## Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Route summary. |
| `PUT` | `/simple/<key>` | Read a small request body into Python text and store it in R2. |
| `GET` | `/simple/<key>` | Fetch a small object as text. |
| `PUT` | `/bytes/<key>` | Read a small body as bytes and store it as a `Uint8Array`. |
| `GET` | `/bytes/<key>` | Fetch a small object and return Python bytes. |
| `PUT` | `/advanced/<key>` | Store bytes with metadata, SHA-256 checksum, and optional storage class. |
| `GET` | `/range/<key>` | Read a byte range with `offset`/`length` or `suffix`. |
| `GET` | `/conditional/<key>` | Conditional get with `?etag=<etag>`. |
| `PUT` | `/objects/<key>` | Store `request.body` directly in R2. |
| `GET` | `/objects/<key>` | Return object metadata as JSON. |
| `GET` | `/objects/<key>/stream` | Stream the R2 object body directly to the response. |
| `GET` | `/objects/<key>/chunks` | Consume R2 stream in Python and report chunk sizes. |
| `DELETE` | `/objects/<key>` | Delete an object. |
| `POST` | `/batch-delete` | Delete keys from a JSON body. |
| `GET` | `/list?prefix=...` | List objects with prefix, limit, cursor, delimiter, and include options. |
| `POST` | `/multipart/<key>?action=create` | Create a multipart upload. |
| `PUT` | `/multipart/<key>?action=upload-part` | Upload one multipart part. |
| `POST` | `/multipart/<key>?action=complete` | Complete a multipart upload. |
| `DELETE` | `/multipart/<key>?action=abort` | Abort a multipart upload. |

## Notes for Python developers

- R2 bindings are JavaScript objects exposed to Python through Pyodide. Results often arrive as `JsProxy` objects.
- Python `bytes` are not automatically valid JavaScript binary data for all Workers APIs. Use `cfboundary.ffi.to_js_bytes()`.
- For large objects, prefer direct JavaScript streams (`request.body` -> R2, R2 `body` -> `Response`) instead of copying bytes into Python memory.
- R2 product features such as CORS, public buckets, lifecycle rules, event notifications, and S3-compatible presigned URLs are important, but they are configuration/client topics and should be separate examples.

See also:

- [`docs/archive/r2-feature-coverage.md`](../../../docs/archive/r2-feature-coverage.md)
- [`docs/api/pythonic-rubric.md`](../../../docs/api/pythonic-rubric.md)
- [`docs/archive/aws-s3-comparison.md`](../../../docs/archive/aws-s3-comparison.md)

## Cloudflare docs

- [R2](https://developers.cloudflare.com/r2/)
- [R2 Workers API](https://developers.cloudflare.com/r2/api/workers/)

## Copy this API

```python
from xampler.r2 import R2Bucket

bucket = R2Bucket(env.BUCKET)
await bucket.object("notes/a.txt").write_text("hello")
text = await bucket.object("notes/a.txt").read_text()
```
