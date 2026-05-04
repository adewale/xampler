"""Experimental helpers for Cloudflare Dynamic Workers.

Dynamic Workers / Worker Loader is currently a beta Cloudflare surface. These
helpers intentionally stay small: they describe the WorkerCode shape and keep
example code from hand-building the same dictionaries everywhere.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal

ModuleKind = Literal["js", "cjs", "py", "text", "data", "json"]


@dataclass(frozen=True)
class DynamicModule:
    """A typed module entry for WorkerCode.modules."""

    kind: ModuleKind
    source: str | bytes | dict[str, Any]

    def to_raw(self) -> dict[str, Any]:
        return {self.kind: self.source}


@dataclass(frozen=True)
class DynamicWorkerLimits:
    """Resource limits for a Dynamic Worker invocation."""

    cpu_ms: int | None = None
    subrequests: int | None = None

    def to_raw(self) -> dict[str, int]:
        raw: dict[str, int] = {}
        if self.cpu_ms is not None:
            raw["cpuMs"] = self.cpu_ms
        if self.subrequests is not None:
            raw["subRequests"] = self.subrequests
        return raw


@dataclass(frozen=True)
class DynamicWorkerCode:
    """Python representation of the Worker Loader `WorkerCode` object."""

    compatibility_date: str
    main_module: str
    modules: dict[str, str | DynamicModule]
    env: dict[str, Any] = field(default_factory=lambda: {})
    compatibility_flags: list[str] = field(default_factory=lambda: [])
    global_outbound: Any | None = None
    limits: DynamicWorkerLimits | None = None

    def to_raw(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "compatibilityDate": self.compatibility_date,
            "mainModule": self.main_module,
            "modules": {
                name: module.to_raw() if isinstance(module, DynamicModule) else module
                for name, module in self.modules.items()
            },
        }
        if self.env:
            raw["env"] = self.env
        if self.compatibility_flags:
            raw["compatibilityFlags"] = self.compatibility_flags
        if self.global_outbound is None:
            raw["globalOutbound"] = None
        else:
            raw["globalOutbound"] = self.global_outbound
        if self.limits is not None:
            raw["limits"] = self.limits.to_raw()
        return raw


def stable_worker_id(prefix: str, code: DynamicWorkerCode | str) -> str:
    """Return a cache-friendly Dynamic Worker id derived from code content."""

    if isinstance(code, DynamicWorkerCode):
        payload = json.dumps(code.to_raw(), sort_keys=True, default=str)
    else:
        payload = code
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def python_fetch_worker(source: str, *, compatibility_date: str) -> DynamicWorkerCode:
    """Build WorkerCode for a Python Worker whose main module is `worker.py`."""

    return DynamicWorkerCode(
        compatibility_date=compatibility_date,
        compatibility_flags=["python_workers", "disable_python_external_sdk"],
        main_module="worker.py",
        modules={"worker.py": source},
        global_outbound=None,
    )
