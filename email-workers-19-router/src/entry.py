from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import js  # type: ignore[import-not-found]
from workers import WorkerEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class IncomingEmail:
    sender: str
    recipient: str
    subject: str | None
    size: int


class EmailRouter:
    def __init__(self, *, forward_to: str, blocked_domains: set[str] | None = None):
        self.forward_to = forward_to
        self.blocked_domains = blocked_domains or set()

    def inspect(self, message: Any) -> IncomingEmail:
        return IncomingEmail(
            sender=str(message.from_),
            recipient=str(message.to),
            subject=message.headers.get("subject"),
            size=int(message.rawSize),
        )

    async def route(self, message: Any) -> IncomingEmail:
        email = self.inspect(message)
        domain = email.sender.rsplit("@", 1)[-1]
        if domain in self.blocked_domains:
            message.setReject("sender domain blocked")
            return email
        headers = js.Headers.new()
        headers.set("X-Processed-By", "xampler-email-workers-19")
        await message.forward(self.forward_to, headers)
        return email


class Default(WorkerEntrypoint):
    async def email(self, message: Any, env: Any, ctx: Any) -> None:
        await EmailRouter(forward_to=str(env.FORWARD_TO)).route(message)
