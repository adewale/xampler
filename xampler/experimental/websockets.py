from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ConnectionState = Literal["connecting", "connected", "disconnected", "error"]


@dataclass(frozen=True)
class WebSocketStatus:
    status: ConnectionState
    source: str
    reconnect: str | None = None


@dataclass(frozen=True)
class WebSocketMessage:
    data: object
    event_type: str = "message"


class DemoWebSocketSession:
    def __init__(self, *, source: str = "demo-websocket-stream"):
        self.source = source
        self.connected = True

    async def status(self) -> WebSocketStatus:
        return WebSocketStatus(
            status="connected" if self.connected else "disconnected",
            source=self.source,
            reconnect="alarm-managed",
        )
