from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, NewType, Protocol, runtime_checkable

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

R2Key = NewType("R2Key", str)
KVKeyName = NewType("KVKeyName", str)
QueueName = NewType("QueueName", str)
WorkflowId = NewType("WorkflowId", str)
VectorId = NewType("VectorId", str)
AgentId = NewType("AgentId", str)

@runtime_checkable
class SupportsRaw(Protocol):
    raw: Any


class DemoTransport[RequestT, ResultT](Protocol):
    async def run(self, request: RequestT) -> ResultT: ...


class RemoteVerifier(Protocol):
    async def verify_remote(self) -> JsonObject: ...


type ProgressCallback = Callable[[int, int], Awaitable[None]]

__all__ = [
    "AgentId",
    "DemoTransport",
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "KVKeyName",
    "ProgressCallback",
    "QueueName",
    "R2Key",
    "RemoteVerifier",
    "SupportsRaw",
    "VectorId",
    "WorkflowId",
]
