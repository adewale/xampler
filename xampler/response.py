from __future__ import annotations

import json
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


def _response_class() -> Any:
    try:
        from workers import Response  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - only used outside Workers by mistake.
        raise RuntimeError("xampler.response helpers require the Python Workers runtime") from exc
    return Response


def response(body: object = "", *, status: int = 200, content_type: str = "text/plain") -> Any:
    return _response_class()(body, {"status": status, "headers": {"content-type": content_type}})


def text_response(body: str, *, status: int = 200) -> Any:
    return response(body, status=status, content_type="text/plain; charset=utf-8")


def html_response(body: str, *, status: int = 200) -> Any:
    return response(body, status=status, content_type="text/html; charset=utf-8")


def json_response(data: object, *, status: int = 200) -> Any:
    cls = _response_class()
    payload = jsonable(data)
    if hasattr(cls, "json"):
        return cls.json(payload, {"status": status})
    return cls(
        json.dumps(payload),
        {"status": status, "headers": {"content-type": "application/json; charset=utf-8"}},
    )


def binary_response(body: object, *, content_type: str, status: int = 200) -> Any:
    return response(body, status=status, content_type=content_type)
