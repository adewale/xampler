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


@dataclass(frozen=True)
class ChatChoice:
    content: str
    model: str
    source: str


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


class DemoAIGateway:
    raw = None

    async def chat(self, request: ChatRequest) -> dict[str, Any]:
        prompt = request.messages[-1].content if request.messages else ""
        choice = ChatChoice(
            content=f"AI Gateway demo response for: {prompt}",
            model=request.model,
            source="demo-ai-gateway",
        )
        return {"choices": [{"message": {"content": choice.content}}], "xampler": asdict(choice)}


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        prompt = "Explain Cloudflare AI Gateway in one sentence."
        chat_request = ChatRequest("openai/gpt-4o-mini", [ChatMessage("user", prompt)])
        if str(request.url).endswith("/demo"):
            return Response.json(await DemoAIGateway().chat(chat_request))
        gateway = AIGateway(
            account_id=str(self.env.ACCOUNT_ID),
            gateway_id=str(self.env.GATEWAY_ID),
            api_key=str(self.env.OPENAI_API_KEY),
        )
        return Response.json(await gateway.chat(chat_request))
