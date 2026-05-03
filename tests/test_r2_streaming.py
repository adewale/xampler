from __future__ import annotations

from typing import Any

import pytest

from xampler.r2 import R2Bucket


class FakeR2Object:
    def __init__(self, chunks: list[bytes]):
        self.key = "data.txt"
        self.size = sum(len(chunk) for chunk in chunks)
        self._chunks = chunks

    async def text(self) -> str:
        return b"".join(self._chunks).decode()

    async def json(self) -> object:
        return {}

    async def chunks(self):  # type: ignore[no-untyped-def]
        for chunk in self._chunks:
            yield chunk


class FakeBucket:
    def __init__(self):
        self.obj = FakeR2Object([b"a", b"bc"])

    async def get(self, key: str, options: Any | None = None) -> FakeR2Object:
        del key, options
        return self.obj


@pytest.mark.asyncio
async def test_r2_byte_stream_helper() -> None:
    stream = await R2Bucket(FakeBucket()).byte_stream("data.txt")
    assert [chunk async for chunk in stream.iter_bytes()] == [b"a", b"bc"]
