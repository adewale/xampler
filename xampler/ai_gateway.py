from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal, cast

from cfboundary.ffi import to_js, to_py

from .cloudflare import RestClient

try:
    import js  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    js = None  # type: ignore[assignment]

ChatRole = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str


@dataclass(frozen=True)
class ChatRequest:
    messages: list[ChatMessage]
    model: str = "openai/gpt-4o-mini"


@dataclass(frozen=True)
class ChatResponse:
    text: str
    raw: dict[str, Any]


class AIGateway(RestClient[Any]):
    """OpenAI-compatible AI Gateway chat client for Workers."""

    api_key: str

    def __init__(self, *, account_id: str, gateway_id: str, api_key: str):
        super().__init__(
            raw=None,
            base_url=(
                f"https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}"
                "/compat/chat/completions"
            ),
        )
        object.__setattr__(self, "api_key", api_key)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if js is None:
            raise RuntimeError("AIGateway requires the Workers runtime js module")
        response = await js.fetch(
            self.base_url,
            to_js({
                "method": "POST",
                "headers": {
                    "authorization": f"Bearer {self.api_key}",
                    "content-type": "application/json",
                },
                "body": json.dumps({
                    "model": request.model,
                    "messages": [asdict(message) for message in request.messages],
                }),
            }),
        )
        raw_data = to_py(await response.json())
        raw = cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}
        return ChatResponse(text=_extract_text(raw), raw=raw)


class DemoAIGateway:
    raw = None

    async def chat(self, request: ChatRequest) -> ChatResponse:
        prompt = request.messages[-1].content if request.messages else ""
        text = f"AI Gateway demo response for: {prompt}"
        return ChatResponse(
            text=text,
            raw={
                "choices": [{"message": {"content": text}}],
                "xampler": {"source": "demo-ai-gateway", "model": request.model},
            },
        )


def _extract_text(raw: dict[str, Any]) -> str:
    raw_choices = raw.get("choices", [])
    choices = cast(list[object], raw_choices) if isinstance(raw_choices, list) else []
    if choices:
        first = choices[0]
        if isinstance(first, dict):
            first_map = cast(dict[object, object], first)
            message = first_map.get("message", {})
            if isinstance(message, dict):
                message_map = cast(dict[object, object], message)
                return str(message_map.get("content", ""))
    return ""
