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
        self.presence: dict[int, dict[str, str]] = {}
        self.max_history = 10
        self.room_name = "lobby"

    async def fetch(self, request: Any) -> Response:
        """Accept WebSockets and provide deterministic dev routes."""

        path = urlparse(str(request.url)).path
        self.room_name = room_name_from_path(path)
        if path.endswith("/dev/history") or path.endswith("/dev/replay"):
            return Response.json({"messages": await self.history()})
        if path.endswith("/dev/presence"):
            return Response.json({
                "presence": list(self.presence.values()),
                "count": len(self.presence),
            })
        if path.endswith("/dev/export"):
            return Response.json({
                "room": self.room_name,
                "transcript": await self.history(),
                "presence": list(self.presence.values()),
            })
        if path.endswith("/dev/seed"):
            seeded = await self.seed_room()
            return Response.json({
                "room": self.room_name,
                "seeded": len(seeded),
                "messages": seeded,
            })
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

        ident = id(server)
        self.presence[ident] = {"username": f"Visitor-{len(self.presence) + 1}", "avatar": "🙂"}
        if self.message_history:
            server.send(
                json.dumps({
                    "type": "replay",
                    "messages": self.message_history,
                    "room": self.room_name,
                })
            )
        self.broadcast_presence()
        server.send(
            json.dumps({
                "type": "system",
                "text": "Connected",
                "room": self.room_name,
                "at": self.now(),
            })
        )
        return Response(None, status=101, web_socket=client)

    async def webSocketMessage(self, ws: Any, message: str) -> None:
        """Normalize each client message, remember it, then broadcast it."""

        data = json.loads(message)
        if data.get("type") == "presence":
            self.presence[id(ws)] = {
                "username": str(data.get("username", "Anonymous")),
                "avatar": str(data.get("avatar", "🙂")),
            }
            self.broadcast_presence()
            return
        event = self.chat_event(data)
        await self.remember(event)
        self.broadcast(json.dumps(event))

    async def webSocketClose(self, ws: Any, code: int, reason: str, was_clean: bool) -> None:
        self.presence.pop(id(ws), None)
        self.broadcast_presence()
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
            "room": self.room_name,
            "at": self.now(),
        }

    async def history(self) -> list[dict[str, str]]:
        return ROOM_MEMORY.get(self.room_name, self.message_history)

    async def remember(self, event: dict[str, str]) -> None:
        history = [*await self.history(), event][-self.max_history :]
        self.message_history = history
        ROOM_MEMORY[self.room_name] = history

    async def seed_room(self) -> list[dict[str, str]]:
        sample_messages = [
            {"username": "Ada", "text": f"Welcome to #{self.room_name}. This is its own DO."},
            {"username": "Linus", "text": "Open another tab in this room to see broadcast."},
            {"username": "Grace", "text": "Switch rooms and the transcript changes."},
            {"username": "Ken", "text": "The Worker uses ROOMS.idFromName(room)."},
        ]
        for message in sample_messages:
            await self.remember(self.chat_event(message))
        history = await self.history()
        self.broadcast(json.dumps({"type": "replay", "room": self.room_name, "messages": history}))
        return history

    def broadcast(self, message: str) -> None:
        for ws in self.ctx.getWebSockets():
            ws.send(message)

    def broadcast_presence(self) -> None:
        self.broadcast(json.dumps({"type": "presence", "users": list(self.presence.values())}))

    def now(self) -> str:
        return datetime.now(UTC).isoformat()


def room_name_from_path(path: str) -> str:
    if not path.startswith("/room/"):
        return "lobby"
    name = path.removeprefix("/room/").split("/", 1)[0]
    return name or "lobby"


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
