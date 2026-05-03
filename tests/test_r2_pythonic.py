from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from xampler.r2 import R2Bucket  # noqa: E402


class FakeR2Object:
    def __init__(
        self,
        key: str,
        body: bytes,
        *,
        content_type: str = "application/octet-stream",
        custom_metadata: dict[str, str] | None = None,
    ):
        self.key = key
        self.body = body
        self.size = len(body)
        self.etag = f"etag-{key}"
        self.httpEtag = f'"etag-{key}"'
        self.httpMetadata = {"contentType": content_type}
        self.customMetadata = custom_metadata or {}

    async def text(self) -> str:
        return self.body.decode()

    async def arrayBuffer(self) -> bytes:
        return self.body

    def to_py(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "size": self.size,
            "etag": self.etag,
            "httpEtag": self.httpEtag,
            "httpMetadata": self.httpMetadata,
            "customMetadata": self.customMetadata,
        }


class FakeR2BucketBinding:
    def __init__(self):
        self.objects: dict[str, FakeR2Object] = {}

    async def put(self, key: str, body: Any, options: dict[str, Any] | None = None) -> FakeR2Object:
        if isinstance(body, str):
            data = body.encode()
        elif isinstance(body, memoryview | bytearray):
            data = bytes(body)
        elif isinstance(body, bytes):
            data = body
        else:
            data = bytes(body)

        options = options or {}
        http_metadata = options.get("httpMetadata", {})
        obj = FakeR2Object(
            key,
            data,
            content_type=http_metadata.get("contentType", "application/octet-stream"),
            custom_metadata=options.get("customMetadata"),
        )
        self.objects[key] = obj
        return obj

    async def get(self, key: str) -> FakeR2Object | None:
        return self.objects.get(key)

    async def head(self, key: str) -> FakeR2Object | None:
        return self.objects.get(key)

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    async def list(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        options = options or {}
        prefix = options.get("prefix", "")
        limit = options.get("limit")
        objects = [
            obj.to_py()
            for key, obj in sorted(self.objects.items())
            if key.startswith(prefix)
        ]
        if limit is not None:
            objects = objects[: int(limit)]
        return {"objects": objects, "truncated": False}


@pytest.mark.asyncio
async def test_text_round_trip_and_metadata() -> None:
    bucket = R2Bucket(FakeR2BucketBinding())

    info = await bucket.put_text("notes/hello.txt", "hello", custom_metadata={"source": "test"})
    text = await bucket.get_text("notes/hello.txt")

    assert text == "hello"
    assert info.key == "notes/hello.txt"
    assert info.size == 5
    assert info.content_type == "text/plain; charset=utf-8"
    assert info.custom_metadata == {"source": "test"}


@pytest.mark.asyncio
async def test_bytes_round_trip_delete_and_missing() -> None:
    bucket = R2Bucket(FakeR2BucketBinding())

    await bucket.put_bytes("blob.bin", b"\x00\x01\x02")
    assert await bucket.get_bytes("blob.bin") == b"\x00\x01\x02"

    await bucket.delete("blob.bin")
    assert await bucket.get("blob.bin") is None
    assert await bucket.head("blob.bin") is None


@pytest.mark.asyncio
async def test_object_handle_and_read_write_aliases() -> None:
    bucket = R2Bucket(FakeR2BucketBinding())
    note = bucket.object("notes/handle.txt")

    await note.write_text("hello handle")

    assert await note.exists() is True
    assert await note.read_text() == "hello handle"
    assert await bucket.read_text("notes/handle.txt") == "hello handle"

    await note.delete()
    assert await note.exists() is False


@pytest.mark.asyncio
async def test_list_prefix_and_limit() -> None:
    bucket = R2Bucket(FakeR2BucketBinding())
    await bucket.put_text("notes/a.txt", "a")
    await bucket.put_text("notes/b.txt", "b")
    await bucket.put_text("images/c.txt", "c")

    result = await bucket.list(prefix="notes/", limit=1)

    assert [obj.key for obj in result.objects] == ["notes/a.txt"]
    assert result.truncated is False
