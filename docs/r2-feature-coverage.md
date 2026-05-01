# R2 Feature Coverage Plan

Last reviewed: 2026-05-01. Python anchor: **Python 3.13**.

Primary R2 sources:

- R2 overview: https://developers.cloudflare.com/r2/
- Workers API reference: https://developers.cloudflare.com/r2/api/workers/workers-api-reference/
- Use R2 from Workers: https://developers.cloudflare.com/r2/api/workers/workers-api-usage/
- Multipart uploads from Workers: https://developers.cloudflare.com/r2/api/workers/workers-multipart-usage/
- S3-compatible API: https://developers.cloudflare.com/r2/api/s3/api/
- Presigned URLs: https://developers.cloudflare.com/r2/api/s3/presigned-urls/
- Public buckets: https://developers.cloudflare.com/r2/buckets/public-buckets/
- CORS: https://developers.cloudflare.com/r2/buckets/cors/
- Event notifications: https://developers.cloudflare.com/r2/buckets/event-notifications/
- Object lifecycle rules: https://developers.cloudflare.com/r2/buckets/object-lifecycles/
- Storage classes: https://developers.cloudflare.com/r2/buckets/storage-classes/
- SSE-C example: https://developers.cloudflare.com/r2/examples/ssec/

## What `r2-01` now covers

| R2 feature | Why it matters | Sample route/API |
|---|---|---|
| Worker binding configuration | The native way Workers access R2. | `r2-01/wrangler.jsonc` binds `BUCKET`. |
| Put small text | First Pythonic happy path. | `PUT /simple/<key>` -> `R2Bucket.put_text()`. |
| Get small text | Native Python `str` return. | `GET /simple/<key>` -> `R2Bucket.get_text()`. |
| Put small bytes | Demonstrates `bytes` -> JS `Uint8Array`. | `PUT /bytes/<key>` -> `R2Bucket.put_bytes()`. |
| Get small bytes | Demonstrates object body consumption. | `GET /bytes/<key>` -> `R2Bucket.get_bytes()`. |
| Streaming upload | Avoids copying large bodies through Python. | `PUT /objects/<key>` -> `request.body` to R2. |
| Streaming download | Returns R2 `ReadableStream` directly. | `GET /objects/<key>/stream`. |
| Python chunk iteration | Shows deliberate stream consumption in Python. | `GET /objects/<key>/chunks`. |
| Head/metadata | Reads metadata without body. | `GET /objects/<key>`. |
| HTTP metadata | Preserves content type. | `put_text()`, `put_bytes()`, `put_stream()`, `PUT /advanced/<key>`. |
| Custom metadata | User-defined object metadata. | `PUT /advanced/<key>`. |
| Checksums | Integrity checking on writes. | `PUT /advanced/<key>` calculates SHA-256. |
| Storage class | Standard vs Infrequent Access. | `PUT /advanced/<key>?ia=1`. |
| Ranged reads | Partial object reads. | `GET /range/<key>?offset=0&length=10`, `?suffix=100`. |
| Conditional get | ETag-based preconditions. | `GET /conditional/<key>?etag=<etag>`. |
| Delete one object | Basic deletion. | `DELETE /objects/<key>`. |
| Delete many objects | R2 supports up to 1000 keys per call. | `POST /batch-delete` with `{"keys": [...]}`. |
| List prefix/limit | Core object discovery. | `GET /list?prefix=notes/&limit=100`. |
| List cursor | Pagination. | `GET /list?cursor=<cursor>`. |
| List delimiter | Folder-like grouping over flat object keys. | `GET /list?delimiter=/`. |
| List include metadata | Include `httpMetadata`/`customMetadata`. | `GET /list?include=httpMetadata,customMetadata`. |
| Multipart create | Large upload workflow. | `POST /multipart/<key>?action=create`. |
| Multipart upload part | Upload individual parts. | `PUT /multipart/<key>?action=upload-part&upload_id=...&part_number=1`. |
| Multipart complete | Assemble parts. | `POST /multipart/<key>?action=complete&upload_id=...`. |
| Multipart abort | Cleanup unfinished upload. | `DELETE /multipart/<key>?action=abort&upload_id=...`. |
| SSE-C | Customer-provided encryption key hook. | Wrapper supports `ssec_key`; README documents that real apps need secret handling. |
| S3-compatible API | Important for boto3/AWS SDK interoperability. | Documented as separate from the Worker binding; future example should cover boto3 against R2. |
| Presigned URLs | S3-compatible feature, not Worker binding-specific. | Future separate client/server sample. |
| Public buckets/custom domains | Bucket-level delivery feature. | Future deployment/config sample. |
| CORS | Browser upload/download integration. | Future deployment/config sample. |
| Event notifications | Bucket events to Queues. | Future Queues + R2 example. |
| Lifecycle rules | Bucket management, not Worker runtime code. | Future Wrangler/API config sample. |

## Documentation structure for R2

`r2-01` should teach in this order:

1. **Mental model**: R2 is object storage; buckets are flat; Workers access buckets through bindings.
2. **Python boundary**: R2 is a JavaScript API in Python Workers; `cfboundary` converts where needed.
3. **Small object helpers**: text and bytes.
4. **Metadata**: HTTP metadata, custom metadata, checksums, storage class.
5. **Read controls**: head, range, conditionals, ETags.
6. **Listing**: prefix, limit, cursor, delimiter, include metadata.
7. **Deletion**: one and many.
8. **Streaming**: direct upload/download, then Python chunk iteration.
9. **Multipart**: create/upload/complete/abort and client responsibilities.
10. **Production bucket features**: CORS, public buckets, lifecycle, notifications, S3 compatibility.

The README should stay runnable and concise. Deeper feature inventory belongs here so the example is not overwhelmed.

## Remaining gaps

The Worker binding sample is now broad, but not every R2 product feature belongs in one Worker file. These should become separate examples:

- **S3-compatible Python client** using boto3 against R2, including presigned URLs.
- **Browser direct upload** with CORS and presigned URLs.
- **R2 event notifications** feeding a Queue and a Python Worker consumer.
- **Public bucket/static delivery** with custom domain notes.
- **Lifecycle/storage management** as configuration-first examples.
