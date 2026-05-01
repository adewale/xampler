from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import js  # type: ignore[import-not-found]
from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ChatRequest:
    model: str
    messages: list[ChatMessage]


class AIGateway:
    def __init__(self, *, account_id: str, gateway_id: str, api_key: str):
        self.url = f"https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/compat/chat/completions"
        self.api_key = api_key

    async def chat(self, request: ChatRequest) -> dict[str, Any]:
        response = await js.fetch(
            self.url,
            to_js({
                "method": "POST",
                "headers": {
                    "authorization": f"Bearer {self.api_key}",
                    "content-type": "application/json",
                },
                "body": json.dumps({
                    "model": request.model,
                    "messages": [asdict(m) for m in request.messages],
                }),
            }),
        )
        return to_py(await response.json())


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        prompt = "Explain Cloudflare AI Gateway in one sentence."
        gateway = AIGateway(
            account_id=str(self.env.ACCOUNT_ID),
            gateway_id=str(self.env.GATEWAY_ID),
            api_key=str(self.env.OPENAI_API_KEY),
        )
        result = await gateway.chat(
            ChatRequest("openai/gpt-4o-mini", [ChatMessage("user", prompt)])
        )
        return Response.json(result)
