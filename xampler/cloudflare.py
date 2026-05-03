from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

RawT = TypeVar("RawT", default=Any)


@dataclass(frozen=True)
class CloudflareService(Generic[RawT]):
    """Base for small wrappers around active Cloudflare bindings or REST clients.

    The base intentionally does very little: examples should keep official
    Cloudflare vocabulary visible and expose the underlying binding/client via
    ``raw`` for features the tutorial wrapper has not modeled yet.
    """

    raw: RawT


@dataclass(frozen=True)
class ResourceRef(Generic[RawT]):
    """Base for passive handles to named Cloudflare resources.

    Examples use refs for things like R2 objects, KV keys, Durable Object stubs,
    Workflow instances, and Agent sessions. The ``name`` is the Python-visible
    handle while ``raw`` remains the platform object/stub.
    """

    name: str
    raw: RawT


@dataclass(frozen=True)
class RestClient(Generic[RawT]):
    """Base for token/HTTP backed product clients.

    Use ``RestClient`` when Worker code calls a Cloudflare REST API directly.
    Use ``CloudflareService`` when wrapping a Worker binding.
    """

    raw: RawT
    base_url: str


__all__ = ["CloudflareService", "ResourceRef", "RestClient"]
