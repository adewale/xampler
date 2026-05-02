from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint


@dataclass(frozen=True)
class TextGenerationRequest:
    prompt: str
    max_tokens: int = 128
    model: str = "@cf/meta/llama-3.1-8b-instruct"

    def inputs(self) -> dict[str, Any]:
        return {"prompt": self.prompt, "max_tokens": self.max_tokens}


@dataclass(frozen=True)
class TextGenerationResponse:
    text: str
    raw: dict[str, Any]

    @classmethod
    def from_workers_ai(cls, data: dict[str, Any]) -> TextGenerationResponse:
        text = str(data.get("response") or data.get("result", {}).get("response") or "")
        return cls(text=text, raw=data)


class AIService:
    """Pythonic wrapper for a Workers AI binding.

    The friendly method returns a typed response while `run()` preserves the
    platform vocabulary and accepts arbitrary model inputs.
    """

    def __init__(self, raw: Any):
        self.raw = raw

    async def run(self, model: str, inputs: dict[str, Any]) -> dict[str, Any]:
        return to_py(await self.raw.run(model, to_js(inputs)))

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        result = await self.run(request.model, request.inputs())
        return TextGenerationResponse.from_workers_ai(result)


class DemoAIService:
    """Deterministic local substitute for verifier coverage without account AI."""

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        text = f"Workers AI response for: {request.prompt}"
        return TextGenerationResponse(text=text, raw={"response": text, "demo": True})


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        prompt = "Explain Cloudflare Workers in one sentence."
        request_data = TextGenerationRequest(prompt)

        if path == "/demo":
            result = await DemoAIService().generate_text(request_data)
            return json_response(asdict(result))

        result = await AIService(self.env.AI).generate_text(request_data)
        return json_response(asdict(result))


def json_response(data: Any) -> Response:
    return Response(json.dumps(data), headers={"content-type": "application/json"})
