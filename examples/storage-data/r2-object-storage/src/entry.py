from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any
from urllib.parse import unquote, urlsplit

from cfboundary.ffi import consume_readable_stream, to_js, to_py

from xampler.r2 import R2Bucket, R2Conditional, R2Range, R2UploadedPart

try:
    import js  # type: ignore[import-not-found]
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:  # Allows local unit tests outside the Workers runtime.
    js = None  # type: ignore[assignment]

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: Any = None


ROUTES = {
    "PUT /simple/<key>": "store a small text body using R2Bucket.put_text()",
    "GET /simple/<key>": "read a small text body using R2Bucket.get_text()",
    "PUT /bytes/<key>": "store a small binary body using to_js_bytes()",
    "GET /bytes/<key>": "read a small binary body into Python bytes",
    "PUT /advanced/<key>": "store bytes with metadata, SHA-256, and storage class",
    "GET /range/<key>?offset=0&length=10": "read a byte range",
    "GET /conditional/<key>?etag=<etag>": "conditional get using an ETag",
    "PUT /objects/<key>": "stream request.body directly into R2",
    "GET /objects/<key>": "return object metadata as JSON",
    "GET /objects/<key>/stream": "stream the R2 body directly to the client",
    "GET /objects/<key>/chunks": "consume the R2 stream in Python and return chunk sizes",
    "DELETE /objects/<key>": "delete an R2 object",
    "POST /batch-delete": "delete up to 1000 keys from a JSON body",
    "GET /list?prefix=...&cursor=...&delimiter=/": "list with pagination/grouping",
    "POST /multipart/<key>?action=create": "create multipart upload",
    "PUT /multipart/<key>?action=upload-part&upload_id=...&part_number=1": "upload a part",
    "POST /multipart/<key>?action=complete&upload_id=...": "complete multipart upload",
    "DELETE /multipart/<key>?action=abort&upload_id=...": "abort multipart upload",
}


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Any:
        bucket = R2Bucket(self.env.BUCKET)
        method = str(getattr(request, "method", "GET")).upper()
        url = urlsplit(str(request.url))
        path = url.path.rstrip("/") or "/"
        params = _query_params(url.query)

        if method == "GET" and path == "/":
            return json_response({"example": "R2 from Python Workers", "routes": ROUTES})

        if method == "GET" and path == "/list":
            return await handle_list(bucket, params)

        if method == "POST" and path == "/batch-delete":
            payload = await request.json()
            keys = [str(key) for key in to_py(payload).get("keys", [])]
            await bucket.delete_many(keys)
            return json_response({"deleted": keys})

        advanced_key = _key_after(path, "/advanced/")
        if advanced_key is not None and method == "PUT":
            body = await consume_readable_stream(request)
            digest = hashlib.sha256(body).hexdigest()
            info = await bucket.put_bytes(
                advanced_key,
                body,
                content_type=_header(request, "content-type") or "application/octet-stream",
                custom_metadata={"example": "advanced", "sha256": digest},
                checksum=("sha256", digest),
                storage_class="InfrequentAccess" if params.get("ia") == "1" else None,
            )
            return json_response({"stored": _asdict_or_none(info), "sha256": digest}, status=201)

        range_key = _key_after(path, "/range/")
        if range_key is not None and method == "GET":
            byte_range = _range_from_params(params)
            body = await bucket.get_bytes(range_key, byte_range=byte_range)
            if body is None:
                return text_response("not found", status=404)
            return binary_response(body, status=206 if byte_range is not None else 200)

        conditional_key = _key_after(path, "/conditional/")
        if conditional_key is not None and method == "GET":
            etag = params.get("etag")
            if not etag:
                return text_response("missing etag query parameter", status=400)
            obj = await bucket.get(
                conditional_key,
                only_if=R2Conditional(etag_matches=etag),
            )
            if obj is None:
                return text_response("not found", status=404)
            if not obj.has_body:
                return text_response("precondition failed", status=412)
            return stream_response(
                obj.raw.body,
                content_type=obj.info.content_type or "application/octet-stream",
                headers={"etag": obj.info.http_etag or obj.info.etag or ""},
            )

        multipart_key = _key_after(path, "/multipart/")
        if multipart_key is not None:
            return await handle_multipart(bucket, request, method, multipart_key, params)

        simple_key = _key_after(path, "/simple/")
        if simple_key is not None:
            return await handle_simple(bucket, request, method, simple_key)

        bytes_key = _key_after(path, "/bytes/")
        if bytes_key is not None:
            return await handle_bytes(bucket, request, method, bytes_key)

        if path.startswith("/objects/"):
            return await handle_object_route(bucket, request, method, path)

        return text_response("not found", status=404)


async def handle_simple(bucket: R2Bucket, request: Any, method: str, key: str) -> Any:
    if method == "PUT":
        text = await request.text()
        info = await bucket.put_text(key, text)
        return json_response({"stored": _asdict_or_none(info)}, status=201)
    if method == "GET":
        text = await bucket.get_text(key)
        if text is None:
            return text_response("not found", status=404)
        return text_response(text)
    return text_response("method not allowed", status=405)


async def handle_bytes(bucket: R2Bucket, request: Any, method: str, key: str) -> Any:
    if method == "PUT":
        body = await consume_readable_stream(request)
        info = await bucket.put_bytes(key, body)
        return json_response({"stored": _asdict_or_none(info)}, status=201)
    if method == "GET":
        body = await bucket.get_bytes(key)
        if body is None:
            return text_response("not found", status=404)
        return binary_response(body)
    return text_response("method not allowed", status=405)


async def handle_list(bucket: R2Bucket, params: dict[str, str]) -> Any:
    try:
        limit = _optional_int(params.get("limit"))
    except ValueError:
        return text_response("limit must be an integer", status=400)

    include = [item for item in params.get("include", "").split(",") if item]
    result = await bucket.list(
        prefix=params.get("prefix"),
        limit=limit,
        cursor=params.get("cursor"),
        delimiter=params.get("delimiter"),
        include=include or None,  # type: ignore[arg-type]
    )
    return json_response(asdict(result))


async def handle_object_route(bucket: R2Bucket, request: Any, method: str, path: str) -> Any:
    if path.endswith("/stream"):
        key = _key_after(path.removesuffix("/stream"), "/objects/")
        if method == "GET" and key:
            obj = await bucket.get(key)
            if obj is None:
                return text_response("not found", status=404)
            return stream_response(
                obj.raw.body,
                content_type=obj.info.content_type or "application/octet-stream",
                headers={"etag": obj.info.http_etag or obj.info.etag or ""},
            )

    if path.endswith("/chunks"):
        key = _key_after(path.removesuffix("/chunks"), "/objects/")
        if method == "GET" and key:
            obj = await bucket.get(key)
            if obj is None:
                return text_response("not found", status=404)
            sizes: list[int] = []
            total = 0
            async for chunk in obj.chunks():
                sizes.append(len(chunk))
                total += len(chunk)
            return json_response({"key": key, "chunks": sizes, "total_bytes": total})

    key = _key_after(path, "/objects/")
    if key is None:
        return text_response("not found", status=404)

    if method == "PUT":
        content_type = _header(request, "content-type") or "application/octet-stream"
        info = await bucket.put_stream(key, request.body, content_type=content_type)
        return json_response({"stored": _asdict_or_none(info)}, status=201)

    if method == "GET":
        info = await bucket.head(key)
        if info is None:
            return text_response("not found", status=404)
        return json_response(asdict(info))

    if method == "DELETE":
        await bucket.delete(key)
        return text_response("deleted")

    return text_response("method not allowed", status=405)


async def handle_multipart(
    bucket: R2Bucket,
    request: Any,
    method: str,
    key: str,
    params: dict[str, str],
) -> Any:
    action = params.get("action")
    upload_id = params.get("upload_id") or params.get("uploadId")

    if method == "POST" and action == "create":
        upload = await bucket.create_multipart_upload(
            key,
            content_type=_header(request, "content-type"),
        )
        return json_response({"key": upload.key, "upload_id": upload.upload_id}, status=201)

    if method == "PUT" and action == "upload-part":
        if not upload_id or not params.get("part_number"):
            return text_response("upload_id and part_number are required", status=400)
        upload = bucket.resume_multipart_upload(key, upload_id)
        part = await upload.upload_part(int(params["part_number"]), request.body)
        return json_response(asdict(part))

    if method == "POST" and action == "complete":
        if not upload_id:
            return text_response("upload_id is required", status=400)
        payload = to_py(await request.json())
        parts = [
            R2UploadedPart(part_number=int(part["part_number"]), etag=str(part["etag"]))
            for part in payload.get("parts", [])
        ]
        upload = bucket.resume_multipart_upload(key, upload_id)
        info = await upload.complete(parts)
        return json_response({"completed": asdict(info)})

    if method == "DELETE" and action == "abort":
        if not upload_id:
            return text_response("upload_id is required", status=400)
        upload = bucket.resume_multipart_upload(key, upload_id)
        await upload.abort()
        return response(None, status=204)

    return text_response("unknown multipart request", status=400)


def _range_from_params(params: dict[str, str]) -> R2Range | None:
    if "suffix" in params:
        return R2Range(suffix=int(params["suffix"]))
    if "offset" in params or "length" in params:
        return R2Range(
            offset=_optional_int(params.get("offset")),
            length=_optional_int(params.get("length")),
        )
    return None


def _key_after(path: str, prefix: str) -> str | None:
    if not path.startswith(prefix):
        return None
    key = unquote(path[len(prefix) :])
    return key or None


def _query_params(query: str) -> dict[str, str]:
    params: dict[str, str] = {}
    for part in query.split("&"):
        if not part:
            continue
        key, _, value = part.partition("=")
        params[unquote(key)] = unquote(value)
    return params


def _optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _header(request: Any, name: str) -> str | None:
    value = request.headers.get(name)
    return None if value is None else str(value)


def _asdict_or_none(value: Any) -> dict[str, Any] | None:
    return None if value is None else asdict(value)


def json_response(data: Any, *, status: int = 200) -> Any:
    return response(json.dumps(data, default=str), status=status, content_type="application/json")


def text_response(
    body: str,
    *,
    status: int = 200,
    content_type: str = "text/plain; charset=utf-8",
) -> Any:
    return response(body, status=status, content_type=content_type)


def binary_response(body: bytes, *, status: int = 200) -> Any:
    return response(body, status=status, content_type="application/octet-stream")


def stream_response(body: Any, *, content_type: str, headers: dict[str, str] | None = None) -> Any:
    clean_headers = {"content-type": content_type}
    clean_headers.update({k: v for k, v in (headers or {}).items() if v})
    return response(body, headers=clean_headers)


def response(
    body: Any,
    *,
    status: int = 200,
    content_type: str | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    final_headers = dict(headers or {})
    if content_type is not None:
        final_headers.setdefault("content-type", content_type)

    if js is None:
        return {"body": body, "status": status, "headers": final_headers}

    return js.Response.new(body, to_js({"status": status, "headers": final_headers}))
