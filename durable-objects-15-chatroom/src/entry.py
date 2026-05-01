from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from js import WebSocketPair  # type: ignore[import-not-found]
from workers import DurableObject, Response, WorkerEntrypoint  # type: ignore[import-not-found]


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
        """Accept one browser WebSocket and attach it to this room."""

        upgrade = request.headers.get("Upgrade")
        if not upgrade or str(upgrade).lower() != "websocket":
            return Response("Expected WebSocket upgrade", status=400)

        # Workers creates WebSockets as a pair. The client side goes back in the
        # HTTP 101 response; the server side stays inside this Durable Object.
        client, server = WebSocketPair.new().object_values()
        self.state.acceptWebSocket(server)

        if self.message_history:
            server.send(json.dumps({"type": "history", "messages": self.message_history}))
        server.send(json.dumps({"type": "system", "text": "Connected", "at": self.now()}))
        return Response(None, status=101, web_socket=client)

    async def webSocketMessage(self, ws: Any, message: str) -> None:
        """Normalize each client message, remember it, then broadcast it."""

        data = json.loads(message)
        event = {
            "type": "message",
            "username": str(data.get("username", "Anonymous")),
            "text": str(data.get("text", "")),
            "at": self.now(),
        }
        self.message_history.append(event)
        self.message_history = self.message_history[-self.max_history :]
        self.broadcast(json.dumps(event))

    async def webSocketClose(self, ws: Any, code: int, reason: str, was_clean: bool) -> None:
        ws.close(code, reason)

    async def webSocketError(self, ws: Any, error: Any) -> None:
        ws.close(1011, "WebSocket error")
        print(f"WebSocket error: {error}")

    def broadcast(self, message: str) -> None:
        for ws in self.state.getWebSockets():
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
