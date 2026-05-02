from __future__ import annotations

import json
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class StreamCheckpoint:
    name: str
    offset: int
    records: int
    status: Literal["running", "complete", "failed"] = "running"


@dataclass(frozen=True)
class AgentEvent:
    type: Literal["token", "tool_call", "done", "error"]
    data: dict[str, Any]


class ByteStream:
    def __init__(self, chunks: AsyncIterable[bytes]):
        self.chunks = chunks

    async def iter_bytes(self) -> AsyncIterator[bytes]:
        async for chunk in self.chunks:
            yield chunk

    async def iter_text(self, encoding: str = "utf-8") -> AsyncIterator[str]:
        async for chunk in self.iter_bytes():
            yield chunk.decode(encoding, errors="replace")

    async def iter_lines(self) -> AsyncIterator[str]:
        carry = ""
        async for text in self.iter_text():
            carry += text
            *lines, carry = carry.split("\n")
            for line in lines:
                yield line
        if carry:
            yield carry


class RecordStream[T]:
    def __init__(self, records: AsyncIterable[T]):
        self.records = records

    async def map[U](self, func: Callable[[T], U]) -> AsyncIterator[U]:
        async for record in self.records:
            yield func(record)

    async def tap(self, func: Callable[[T], Awaitable[None]]) -> AsyncIterator[T]:
        async for record in self.records:
            await func(record)
            yield record

    async def batch(self, size: int) -> AsyncIterator[list[T]]:
        batch: list[T] = []
        async for record in self.records:
            batch.append(record)
            if len(batch) >= size:
                yield batch
                batch = []
        if batch:
            yield batch


class JsonlReader:
    def __init__(self, lines: AsyncIterable[str]):
        self.lines = lines

    async def records(self) -> AsyncIterator[dict[str, Any]]:
        async for line in self.lines:
            if line.strip():
                yield json.loads(line)


async def aiter_batches[T](records: AsyncIterable[T], size: int) -> AsyncIterator[list[T]]:
    async for batch in RecordStream(records).batch(size):
        yield batch


async def async_enumerate[T](
    iterable: AsyncIterable[T], start: int = 0
) -> AsyncIterator[tuple[int, T]]:
    index = start
    async for item in iterable:
        yield index, item
        index += 1
