from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint


@dataclass(frozen=True)
class TextGenerationRequest:
    prompt: str
    max_tokens: int = 128

class AIService:
    def __init__(self, raw: Any): self.raw = raw
    async def generate_text(self, request: TextGenerationRequest) -> dict[str, Any]:
        return to_py(await self.raw.run("@cf/meta/llama-3.1-8b-instruct", to_js(request.__dict__)))

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        request_data = TextGenerationRequest(
            "Explain Cloudflare Workers in one sentence."
        )
        result = await AIService(self.env.AI).generate_text(request_data)
        return Response(json.dumps(result), headers={"content-type": "application/json"})
