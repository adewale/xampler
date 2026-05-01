from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urlparse

import js  # type: ignore[import-not-found]
from pyodide.ffi import create_proxy  # type: ignore[import-not-found]
from workers import DurableObject, Response, WorkerEntrypoint  # type: ignore[import-not-found]


class StreamConsumer(DurableObject):
    """A Durable Object that owns one long-lived outbound WebSocket.

    Literate note: a normal Worker request is short-lived. A Durable Object gives
    us one named, stateful actor that can keep connection state and use alarms to
    reconnect if the process is evicted or the socket closes.
    """

    def __init__(self, state: Any, env: Any):
        super().__init__(state, env)
        self.websocket: Any = None
        self.connected = False
        self.last_print_time = 0.0

    async def fetch(self, request: Any) -> Response:
        """Expose a tiny HTTP API for inspecting/starting the consumer."""

        # The first request is our lazy initialization point. We connect only when
        # someone asks for this Durable Object, then alarms keep it warm enough to
        # reconnect when necessary.
        if not self.connected:
            await self._schedule_next_alarm()
            await self._connect()

        path = urlparse(str(request.url)).path
        if path == "/status":
            return Response("connected" if self.connected else "disconnected")
        return Response("Available endpoint: /status")

    async def alarm(self) -> None:
        """Durable Object alarm: periodically ensure the stream is connected."""

        if not self.connected:
            await self._connect()
        await self._schedule_next_alarm()

    async def _schedule_next_alarm(self) -> None:
        # Alarms use millisecond timestamps.
        await self.ctx.storage.setAlarm(int(time.time() * 1000) + 60_000)

    async def _connect(self) -> None:
        # Bluesky Jetstream is a convenient public WebSocket stream. We filter to
        # post commits so local logs stay readable.
        url = "wss://jetstream2.us-east.bsky.network/subscribe"
        url += "?wantedCollections=app.bsky.feed.post"
        self.websocket = js.WebSocket.new(url)

        # Pyodide needs proxies when Python callables cross into JS event APIs.
        # The Durable Object owns these for its lifetime, so we intentionally do
        # not destroy them until the object is evicted/restarted.
        self.websocket.addEventListener("open", create_proxy(self._on_open))
        self.websocket.addEventListener("message", create_proxy(self._on_message))
        self.websocket.addEventListener("error", create_proxy(self._on_error))
        self.websocket.addEventListener("close", create_proxy(self._on_close))

    def _on_open(self, event: Any) -> None:
        self.connected = True
        print("Connected to Bluesky Jetstream")

    def _on_message(self, event: Any) -> None:
        # Keep the example gentle: parse messages, filter posts, and log at most
        # once per second. Real apps would enqueue or persist events here.
        try:
            data = json.loads(str(event.data))
            commit = data.get("commit", {})
            if commit.get("collection") != "app.bsky.feed.post":
                return
            now = time.time()
            if now - self.last_print_time >= 1.0:
                print("Post record", commit.get("record", {}))
                self.last_print_time = now
        except Exception as exc:  # noqa: BLE001 - log and keep consuming.
            print(f"Could not process stream message: {exc}")

    def _on_error(self, event: Any) -> None:
        self.connected = False
        print(f"WebSocket error: {event}")

    def _on_close(self, event: Any) -> None:
        self.connected = False
        print(f"WebSocket closed: {event}")


class Default(WorkerEntrypoint):
    """Route every request to the singleton consumer Durable Object."""

    async def fetch(self, request: Any) -> Any:
        namespace = self.env.CONSUMER
        stub = namespace.get(namespace.idFromName("global-stream-consumer"))
        return await stub.fetch(request)
