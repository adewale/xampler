from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any, cast


def jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return cast(object, asdict(value))
    if isinstance(value, list):
        return [jsonable(item) for item in cast(list[object], value)]
    if isinstance(value, tuple):
        return [jsonable(item) for item in cast(tuple[object, ...], value)]
    if isinstance(value, dict):
        mapping = cast(Mapping[object, object], value)
        return {str(key): jsonable(item) for key, item in mapping.items()}
    return value


def error_payload(message: str, *, status: int = 400, code: str = "bad_request") -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "status": status}}
