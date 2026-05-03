from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cloudflare import CloudflareService


@dataclass(frozen=True)
class RpcCall:
    method: str
    args: tuple[object, ...] = ()


@dataclass(frozen=True)
class RpcResult:
    method: str
    value: object


class ServiceBinding(CloudflareService[Any]):
    """Small wrapper for calling RPC-style methods on a Service Binding."""

    async def call(self, method: str, *args: object) -> RpcResult:
        target = getattr(self.raw, method)
        return RpcResult(method=method, value=await target(*args))

    async def fetch(self, request: Any) -> Any:
        return await self.raw.fetch(request)


class DemoServiceBinding:
    async def call(self, method: str, *args: object) -> RpcResult:
        return RpcResult(method=method, value={"demo": True, "args": list(args)})
