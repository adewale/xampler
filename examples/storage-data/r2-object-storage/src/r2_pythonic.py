"""Small Pythonic layer over a Cloudflare R2 bucket binding.

R2's runtime API is JavaScript-first. In Python Workers, that API is exposed through
Pyodide, so values crossing the boundary may be JsProxy objects, JavaScript null, or
JavaScript streams. This module keeps those conversions at the edge.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Literal, Self

from cfboundary.ffi import (
    consume_readable_stream,
    get_r2_size,
    is_js_missing,
    stream_r2_body,
    to_js,
    to_js_bytes,
    to_py,
)

StorageClass = Literal["Standard", "InfrequentAccess"]
ChecksumAlgorithm = Literal["md5", "sha1", "sha256", "sha384", "sha512"]
MetadataField = Literal["httpMetadata", "customMetadata"]


@dataclass(frozen=True, kw_only=True)
class R2HttpMetadata:
    """HTTP metadata stored with an R2 object.

    Python code uses snake_case. `to_options()` emits the camelCase shape used by
    the Workers R2 API.
    """

    content_type: str | None = None
    content_language: str | None = None
    content_disposition: str | None = None
    content_encoding: str | None = None
    cache_control: str | None = None
    cache_expiry: Any = None

    def to_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if self.content_type is not None:
            options["contentType"] = self.content_type
        if self.content_language is not None:
            options["contentLanguage"] = self.content_language
        if self.content_disposition is not None:
            options["contentDisposition"] = self.content_disposition
        if self.content_encoding is not None:
            options["contentEncoding"] = self.content_encoding
        if self.cache_control is not None:
            options["cacheControl"] = self.cache_control
        if self.cache_expiry is not None:
            options["cacheExpiry"] = self.cache_expiry
        return options


@dataclass(frozen=True, kw_only=True)
class R2Range:
    """Byte range for an R2 read.

    Use either `offset` with optional `length`, or `suffix` for the final N bytes.
    """

    offset: int | None = None
    length: int | None = None
    suffix: int | None = None

    def to_options(self) -> dict[str, int]:
        if self.suffix is not None:
            return {"suffix": self.suffix}
        options: dict[str, int] = {}
        if self.offset is not None:
            options["offset"] = self.offset
        if self.length is not None:
            options["length"] = self.length
        return options


@dataclass(frozen=True, kw_only=True)
class R2Conditional:
    """ETag/date preconditions for R2 get/put operations."""

    etag_matches: str | None = None
    etag_does_not_match: str | None = None
    uploaded_before: Any = None
    uploaded_after: Any = None

    def to_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if self.etag_matches is not None:
            options["etagMatches"] = self.etag_matches
        if self.etag_does_not_match is not None:
            options["etagDoesNotMatch"] = self.etag_does_not_match
        if self.uploaded_before is not None:
            options["uploadedBefore"] = self.uploaded_before
        if self.uploaded_after is not None:
            options["uploadedAfter"] = self.uploaded_after
        return options


@dataclass(frozen=True)
class R2ObjectInfo:
    """Python metadata for an R2 object or object head."""

    key: str
    size: int | None
    etag: str | None = None
    http_etag: str | None = None
    uploaded: Any = None
    http_metadata: R2HttpMetadata | None = None
    content_type: str | None = None
    custom_metadata: dict[str, Any] | None = None
    storage_class: str | None = None
    range: dict[str, Any] | None = None
    checksums: dict[str, Any] | None = None


@dataclass(frozen=True)
class R2ListResult:
    """Python representation of an R2 list response."""

    objects: list[R2ObjectInfo]
    truncated: bool
    cursor: str | None = None
    delimited_prefixes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class R2UploadedPart:
    """Python representation of an uploaded multipart part."""

    part_number: int
    etag: str

    def to_options(self) -> dict[str, Any]:
        return {"partNumber": self.part_number, "etag": self.etag}


class R2Object:
    """A fetched R2 object with Python-friendly helpers.

    `raw` is intentionally exposed for JavaScript-native streaming and advanced R2
    features. Use the Python helpers for small objects and `raw.body` for large
    streaming responses.
    """

    def __init__(self, raw: Any):
        self.raw = raw
        self.info = object_info(raw)

    @property
    def has_body(self) -> bool:
        """False when a conditional `get()` found metadata but withheld the body."""

        return not is_js_missing(getattr(self.raw, "body", None))

    async def text(self) -> str:
        return str(await self.raw.text())

    async def json(self) -> Any:
        return to_py(await self.raw.json())

    async def bytes(self) -> bytes:
        return await consume_readable_stream(self.raw)

    async def chunks(self) -> AsyncIterator[bytes]:
        async for chunk in stream_r2_body(self.raw):
            yield chunk


class R2ObjectRef:
    """A lightweight handle for one R2 key.

    This borrows from `pathlib`: construct a reference cheaply, then call methods
    such as `read_text()`, `write_bytes()`, `exists()`, and `stat()`.
    """

    def __init__(self, bucket: R2Bucket, key: str):
        self.bucket = bucket
        self.key = key

    async def read_text(self) -> str | None:
        return await self.bucket.get_text(self.key)

    async def write_text(self, value: str, **kwargs: Any) -> R2ObjectInfo | None:
        return await self.bucket.put_text(self.key, value, **kwargs)

    async def read_json(self) -> Any | None:
        return await self.bucket.get_json(self.key)

    async def read_bytes(self, *, byte_range: R2Range | None = None) -> bytes | None:
        return await self.bucket.get_bytes(self.key, byte_range=byte_range)

    async def write_bytes(
        self,
        value: bytes | bytearray | memoryview,
        **kwargs: Any,
    ) -> R2ObjectInfo | None:
        return await self.bucket.put_bytes(self.key, value, **kwargs)

    async def stat(self) -> R2ObjectInfo | None:
        return await self.bucket.head(self.key)

    async def exists(self) -> bool:
        return await self.stat() is not None

    async def delete(self) -> None:
        await self.bucket.delete(self.key)

    async def get(self, **kwargs: Any) -> R2Object | None:
        return await self.bucket.get(self.key, **kwargs)


class R2MultipartUpload:
    """Pythonic façade for an in-progress R2 multipart upload.

    Supports `async with` so unfinished multipart uploads are aborted when an
    exception leaves the block before `complete()` is called.
    """

    def __init__(self, raw_upload: Any):
        self.raw = raw_upload
        self.key = str(raw_upload.key)
        self.upload_id = str(raw_upload.uploadId)
        self.completed = False
        self.aborted = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None and not self.completed and not self.aborted:
            await self.abort()

    async def upload_part(self, part_number: int, body: Any) -> R2UploadedPart:
        raw = await self.raw.uploadPart(part_number, body)
        data = to_py(raw)
        return R2UploadedPart(
            part_number=int(data.get("partNumber", part_number)),
            etag=str(data.get("etag", getattr(raw, "etag", ""))),
        )

    async def complete(self, parts: list[R2UploadedPart]) -> R2ObjectInfo:
        raw = await self.raw.complete(to_js([part.to_options() for part in parts]))
        self.completed = True
        return object_info(raw, fallback_key=self.key)

    async def abort(self) -> None:
        await self.raw.abort()
        self.aborted = True


class R2Bucket:
    """Pythonic façade for an R2 bucket binding."""

    def __init__(self, raw_bucket: Any):
        self.raw = raw_bucket

    def object(self, key: str) -> R2ObjectRef:
        """Return a pathlib-like handle for one object key."""

        return R2ObjectRef(self, key)

    async def write_text(self, key: str, value: str, **kwargs: Any) -> R2ObjectInfo | None:
        return await self.put_text(key, value, **kwargs)

    async def read_text(self, key: str) -> str | None:
        return await self.get_text(key)

    async def write_bytes(
        self,
        key: str,
        value: bytes | bytearray | memoryview,
        **kwargs: Any,
    ) -> R2ObjectInfo | None:
        return await self.put_bytes(key, value, **kwargs)

    async def read_bytes(
        self,
        key: str,
        *,
        byte_range: R2Range | None = None,
    ) -> bytes | None:
        return await self.get_bytes(key, byte_range=byte_range)

    async def exists(self, key: str) -> bool:
        return await self.head(key) is not None

    async def put_text(
        self,
        key: str,
        value: str,
        *,
        content_type: str = "text/plain; charset=utf-8",
        http_metadata: R2HttpMetadata | None = None,
        custom_metadata: dict[str, str] | None = None,
        only_if: R2Conditional | Any | None = None,
        storage_class: StorageClass | None = None,
    ) -> R2ObjectInfo | None:
        return await self.put(
            key,
            value,
            content_type=content_type,
            http_metadata=http_metadata,
            custom_metadata=custom_metadata,
            only_if=only_if,
            storage_class=storage_class,
        )

    async def put_bytes(
        self,
        key: str,
        value: bytes | bytearray | memoryview,
        *,
        content_type: str = "application/octet-stream",
        http_metadata: R2HttpMetadata | None = None,
        custom_metadata: dict[str, str] | None = None,
        only_if: R2Conditional | Any | None = None,
        checksum: tuple[ChecksumAlgorithm, str] | None = None,
        storage_class: StorageClass | None = None,
    ) -> R2ObjectInfo | None:
        return await self.put(
            key,
            to_js_bytes(value),
            content_type=content_type,
            http_metadata=http_metadata,
            custom_metadata=custom_metadata,
            only_if=only_if,
            checksum=checksum,
            storage_class=storage_class,
        )

    async def put_stream(
        self,
        key: str,
        body: Any,
        *,
        content_type: str = "application/octet-stream",
        http_metadata: R2HttpMetadata | None = None,
        custom_metadata: dict[str, str] | None = None,
        only_if: R2Conditional | Any | None = None,
        storage_class: StorageClass | None = None,
    ) -> R2ObjectInfo | None:
        """Store a JavaScript ReadableStream directly in R2.

        This is the path to prefer for larger uploads. The stream stays on the
        JavaScript side instead of being copied through Python memory.
        """

        return await self.put(
            key,
            body,
            content_type=content_type,
            http_metadata=http_metadata,
            custom_metadata=custom_metadata,
            only_if=only_if,
            storage_class=storage_class,
        )

    async def put(
        self,
        key: str,
        body: Any,
        *,
        content_type: str | None = None,
        http_metadata: R2HttpMetadata | None = None,
        custom_metadata: dict[str, str] | None = None,
        only_if: R2Conditional | Any | None = None,
        checksum: tuple[ChecksumAlgorithm, str] | None = None,
        storage_class: StorageClass | None = None,
        ssec_key: str | None = None,
    ) -> R2ObjectInfo | None:
        options = _write_options(
            content_type=content_type,
            http_metadata=http_metadata,
            custom_metadata=custom_metadata,
            only_if=only_if,
            checksum=checksum,
            storage_class=storage_class,
            ssec_key=ssec_key,
        )
        raw = (
            await self.raw.put(key, body, to_js(options))
            if options
            else await self.raw.put(key, body)
        )
        if is_js_missing(raw):
            return None
        return object_info(raw, fallback_key=key)

    async def get(
        self,
        key: str,
        *,
        byte_range: R2Range | None = None,
        only_if: R2Conditional | Any | None = None,
        ssec_key: str | None = None,
    ) -> R2Object | None:
        options: dict[str, Any] = {}
        if byte_range is not None:
            options["range"] = byte_range.to_options()
        if only_if is not None:
            options["onlyIf"] = _conditional_options(only_if)
        if ssec_key is not None:
            options["ssecKey"] = ssec_key

        raw = await self.raw.get(key, to_js(options)) if options else await self.raw.get(key)
        if is_js_missing(raw):
            return None
        return R2Object(raw)

    async def head(self, key: str) -> R2ObjectInfo | None:
        raw = await self.raw.head(key)
        if is_js_missing(raw):
            return None
        return object_info(raw, fallback_key=key)

    async def get_text(self, key: str) -> str | None:
        obj = await self.get(key)
        return None if obj is None else await obj.text()

    async def get_json(self, key: str) -> Any | None:
        obj = await self.get(key)
        return None if obj is None else await obj.json()

    async def get_bytes(self, key: str, *, byte_range: R2Range | None = None) -> bytes | None:
        obj = await self.get(key, byte_range=byte_range)
        return None if obj is None else await obj.bytes()

    async def delete(self, key: str) -> None:
        await self.raw.delete(key)

    async def delete_many(self, keys: list[str]) -> None:
        await self.raw.delete(to_js(keys))

    async def list(
        self,
        *,
        prefix: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        delimiter: str | None = None,
        include: list[MetadataField] | None = None,
    ) -> R2ListResult:
        options: dict[str, Any] = {}
        if prefix is not None:
            options["prefix"] = prefix
        if limit is not None:
            options["limit"] = limit
        if cursor is not None:
            options["cursor"] = cursor
        if delimiter is not None:
            options["delimiter"] = delimiter
        if include is not None:
            options["include"] = include

        raw = await self.raw.list(to_js(options)) if options else await self.raw.list()
        data = to_py(raw)
        objects = [object_info(item) for item in data.get("objects", [])]
        return R2ListResult(
            objects=objects,
            truncated=bool(data.get("truncated", False)),
            cursor=data.get("cursor"),
            delimited_prefixes=list(data.get("delimitedPrefixes", [])),
        )

    async def iter_objects(
        self,
        *,
        prefix: str | None = None,
        delimiter: str | None = None,
        include: list[MetadataField] | None = None,
        page_size: int = 1000,
    ) -> AsyncIterator[R2ObjectInfo]:
        """Yield matching objects across all list pages."""

        cursor: str | None = None
        while True:
            page = await self.list(
                prefix=prefix,
                limit=page_size,
                cursor=cursor,
                delimiter=delimiter,
                include=include,
            )
            for item in page.objects:
                yield item
            if not page.truncated:
                break
            cursor = page.cursor

    async def create_multipart_upload(
        self,
        key: str,
        *,
        content_type: str | None = None,
        http_metadata: R2HttpMetadata | None = None,
        custom_metadata: dict[str, str] | None = None,
        storage_class: StorageClass | None = None,
        ssec_key: str | None = None,
    ) -> R2MultipartUpload:
        options = _write_options(
            content_type=content_type,
            http_metadata=http_metadata,
            custom_metadata=custom_metadata,
            storage_class=storage_class,
            ssec_key=ssec_key,
        )
        raw = (
            await self.raw.createMultipartUpload(key, to_js(options))
            if options
            else await self.raw.createMultipartUpload(key)
        )
        return R2MultipartUpload(raw)

    def resume_multipart_upload(self, key: str, upload_id: str) -> R2MultipartUpload:
        return R2MultipartUpload(self.raw.resumeMultipartUpload(key, upload_id))


def object_info(raw: Any, *, fallback_key: str | None = None) -> R2ObjectInfo:
    """Convert an R2 object/head/write result into Python metadata."""

    data = to_py(raw)
    if not isinstance(data, dict):
        data = {}

    raw_http_metadata = data.get("httpMetadata") or {}
    http_metadata = _http_metadata_from_options(raw_http_metadata)
    custom_metadata = data.get("customMetadata") or None
    checksums = data.get("checksums") or None

    return R2ObjectInfo(
        key=str(data.get("key") or getattr(raw, "key", fallback_key) or fallback_key or ""),
        size=get_r2_size(raw) if not isinstance(data.get("size"), int) else int(data["size"]),
        etag=data.get("etag") or _optional_str(getattr(raw, "etag", None)),
        http_etag=data.get("httpEtag") or _optional_str(getattr(raw, "httpEtag", None)),
        uploaded=_optional_str(data.get("uploaded") or getattr(raw, "uploaded", None)),
        http_metadata=http_metadata,
        content_type=http_metadata.content_type if http_metadata is not None else None,
        custom_metadata=custom_metadata if isinstance(custom_metadata, dict) else None,
        storage_class=data.get("storageClass") or _optional_str(getattr(raw, "storageClass", None)),
        range=data.get("range") if isinstance(data.get("range"), dict) else None,
        checksums=checksums if isinstance(checksums, dict) else None,
    )


def _write_options(
    *,
    content_type: str | None = None,
    http_metadata: R2HttpMetadata | None = None,
    custom_metadata: dict[str, str] | None = None,
    only_if: R2Conditional | Any | None = None,
    checksum: tuple[ChecksumAlgorithm, str] | None = None,
    storage_class: StorageClass | None = None,
    ssec_key: str | None = None,
) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if http_metadata is not None:
        options["httpMetadata"] = http_metadata.to_options()
    if content_type:
        options.setdefault("httpMetadata", {})["contentType"] = content_type
    if custom_metadata:
        options["customMetadata"] = custom_metadata
    if only_if is not None:
        options["onlyIf"] = _conditional_options(only_if)
    if checksum is not None:
        algorithm, value = checksum
        options[algorithm] = value
    if storage_class is not None:
        options["storageClass"] = storage_class
    if ssec_key is not None:
        options["ssecKey"] = ssec_key
    return options


def _http_metadata_from_options(value: Any) -> R2HttpMetadata | None:
    if not isinstance(value, dict) or not value:
        return None
    return R2HttpMetadata(
        content_type=value.get("contentType"),
        content_language=value.get("contentLanguage"),
        content_disposition=value.get("contentDisposition"),
        content_encoding=value.get("contentEncoding"),
        cache_control=value.get("cacheControl"),
        cache_expiry=value.get("cacheExpiry"),
    )


def _conditional_options(value: R2Conditional | Any) -> Any:
    return value.to_options() if isinstance(value, R2Conditional) else value


def _optional_str(value: Any) -> str | None:
    if is_js_missing(value):
        return None
    return None if value is None else str(value)
