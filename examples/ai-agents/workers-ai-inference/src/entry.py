from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.ai import AIService, DemoAIService, TextGenerationRequest
from xampler.response import jsonable


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        prompt = "Explain Cloudflare Workers in one sentence."
        request_data = TextGenerationRequest(prompt)

        if path == "/demo":
            result = await DemoAIService().generate_text(request_data)
            return Response.json(jsonable(result))

        result = await AIService(self.env.AI).generate_text(request_data)
        return Response.json(jsonable(result))
