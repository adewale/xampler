from __future__ import annotations

from typing import Any

from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.ai_gateway import AIGateway, ChatMessage, ChatRequest, DemoAIGateway


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        prompt = "Explain Cloudflare AI Gateway in one sentence."
        model = str(getattr(self.env, "MODEL", "openai/gpt-4o-mini"))
        chat_request = ChatRequest(messages=[ChatMessage("user", prompt)], model=model)
        if str(request.url).endswith("/demo"):
            return Response.json((await DemoAIGateway().chat(chat_request)).raw)
        gateway = AIGateway(
            account_id=str(self.env.ACCOUNT_ID),
            gateway_id=str(self.env.GATEWAY_ID),
            api_key=str(self.env.OPENAI_API_KEY),
        )
        return Response.json((await gateway.chat(chat_request)).raw)
