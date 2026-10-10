"""`xampler.response` against the call shape of the real `workers.Response`.

The real class ships in workers-runtime-sdk and only runs inside Pyodide, so this test
installs a stand-in with the same signature. In workers-runtime-sdk 1.9.0, the static
`Response.json(data, ...)` delegates to `Response.from_json(data, status=200,
status_text="", headers=None)`. A positional init dict, which `json_response` once
passed, lands in `status`, and the runtime rejects it with HTTP 500. The local runtime
verifier found that; this test catches it without starting a Worker.
"""

from __future__ import annotations

import sys
import types
from http import HTTPStatus

import pytest

from xampler.response import json_response


class RuntimeShapedResponse:
    def __init__(self, data: object, status: int) -> None:
        self.data = data
        self.status = status

    @staticmethod
    def json(
        data: object,
        status: HTTPStatus | int = HTTPStatus.OK,
        status_text: str = "",
        headers: object = None,
    ) -> RuntimeShapedResponse:
        if not isinstance(status, int):
            raise TypeError(f"Response status must be an int, got {type(status).__name__}")
        return RuntimeShapedResponse(data, int(status))


@pytest.fixture(autouse=True)
def workers_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    module = types.ModuleType("workers")
    monkeypatch.setattr(module, "Response", RuntimeShapedResponse, raising=False)
    monkeypatch.setitem(sys.modules, "workers", module)


def test_json_response_passes_status_to_runtime_json() -> None:
    created = json_response({"created": True}, status=201)
    assert isinstance(created, RuntimeShapedResponse)
    assert created.status == 201
    assert created.data == {"created": True}

    ok = json_response(("a", 1))
    assert isinstance(ok, RuntimeShapedResponse)
    assert ok.status == 200
    assert ok.data == ["a", 1]
