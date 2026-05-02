from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from js import WebSocketPair  # type: ignore[import-not-found]
from workers import DurableObject, Response, WorkerEntrypoint  # type: ignore[import-not-found]

ROOM_MEMORY: dict[str, list[dict[str, str]]] = {}


class ChatRoom(DurableObject):
    """A room is one Durable Object instance.

    Literate note: Durable Objects are a natural home for WebSocket coordination
    because every client in the same room talks to the same stateful actor.
    """

    def __init__(self, state: Any, env: Any):
        super().__init__(state, env)
        self.message_history: list[dict[str, str]] = []
        self.max_history = 50

    async def fetch(self, request: Any) -> Response:
        """Accept WebSockets and provide deterministic dev routes."""

        path = urlparse(str(request.url)).path
        if path.endswith("/dev/history"):
            return Response.json({"messages": await self.history()})
        if path.endswith("/dev/send") and request.method == "POST":
            data = json.loads(await request.text())
            event = self.chat_event(data)
            await self.remember(event)
            self.broadcast(json.dumps(event))
            return Response.json(event)

        upgrade = request.headers.get("Upgrade")
        if not upgrade or str(upgrade).lower() != "websocket":
            return Response("Expected WebSocket upgrade", status=400)

        # Workers creates WebSockets as a pair. The client side goes back in the
        # HTTP 101 response; the server side stays inside this Durable Object.
        client, server = WebSocketPair.new().object_values()
        self.ctx.acceptWebSocket(server)

        if self.message_history:
            server.send(json.dumps({"type": "history", "messages": self.message_history}))
        server.send(json.dumps({"type": "system", "text": "Connected", "at": self.now()}))
        return Response(None, status=101, web_socket=client)

    async def webSocketMessage(self, ws: Any, message: str) -> None:
        """Normalize each client message, remember it, then broadcast it."""

        event = self.chat_event(json.loads(message))
        await self.remember(event)
        self.broadcast(json.dumps(event))

    async def webSocketClose(self, ws: Any, code: int, reason: str, was_clean: bool) -> None:
        safe_code = 1000 if code in {1005, 1006} else code
        ws.close(safe_code, reason)

    async def webSocketError(self, ws: Any, error: Any) -> None:
        ws.close(1011, "WebSocket error")
        print(f"WebSocket error: {error}")

    def chat_event(self, data: dict[str, Any]) -> dict[str, str]:
        return {
            "type": "message",
            "username": str(data.get("username", "Anonymous")),
            "text": str(data.get("text", "")),
            "at": self.now(),
        }

    async def history(self) -> list[dict[str, str]]:
        stored = await self.ctx.storage.get("message_history")
        if stored:
            return json.loads(str(stored))
        return ROOM_MEMORY.get("demo", self.message_history)

    async def remember(self, event: dict[str, str]) -> None:
        history = [*await self.history(), event][-self.max_history :]
        self.message_history = history
        ROOM_MEMORY["demo"] = history
        await self.ctx.storage.put("message_history", json.dumps(history))

    def broadcast(self, message: str) -> None:
        for ws in self.ctx.getWebSockets():
            ws.send(message)

    def now(self) -> str:
        return datetime.now(UTC).isoformat()


class Default(WorkerEntrypoint):
    """Serve the client page and route `/room/<name>` to the matching room."""

    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path == "/":
            html = (Path(__file__).parent / "chatroom.html").read_text()
            return Response(html, headers={"content-type": "text/html"})

        if path.startswith("/room/"):
            room_name = path.removeprefix("/room/")
            if not room_name:
                return Response("Room name required", status=400)
            namespace = self.env.ROOMS
            stub = namespace.get(namespace.idFromName(room_name))
            return await stub.fetch(request)

        return Response("Not found. Open / or connect to /room/<name>.", status=404)
