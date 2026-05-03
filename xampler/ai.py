from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from cfboundary.ffi import to_js, to_py

from xampler.cloudflare import CloudflareService
from xampler.types import DemoTransport


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
        result = data.get("result", {})
        result_data = cast(dict[str, Any], result) if isinstance(result, dict) else {}
        text = str(data.get("response") or result_data.get("response") or "")
        return cls(text=text, raw=data)


class AIService(CloudflareService[Any]):
    """Pythonic wrapper for a Workers AI binding."""

    async def run(self, model: str, inputs: dict[str, Any]) -> dict[str, Any]:
        raw_data = to_py(await self.raw.run(model, to_js(inputs)))
        return cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        result = await self.run(request.model, request.inputs())
        return TextGenerationResponse.from_workers_ai(result)


class DemoAIService(DemoTransport[TextGenerationRequest, TextGenerationResponse]):
    """Deterministic local substitute for verifier coverage without account AI."""

    async def run(self, request: TextGenerationRequest) -> TextGenerationResponse:
        text = f"Workers AI response for: {request.prompt}"
        return TextGenerationResponse(text=text, raw={"response": text, "demo": True})

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        return await self.run(request)


__all__ = ["AIService", "DemoAIService", "TextGenerationRequest", "TextGenerationResponse"]
