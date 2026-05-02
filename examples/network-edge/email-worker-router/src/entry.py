from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import js  # type: ignore[import-not-found]
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class IncomingEmail:
    sender: str
    recipient: str
    subject: str | None
    size: int


@dataclass(frozen=True)
class EmailDecision:
    action: str
    reason: str
    email: IncomingEmail


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

    def decide(self, email: IncomingEmail) -> EmailDecision:
        domain = email.sender.rsplit("@", 1)[-1]
        if domain in self.blocked_domains:
            return EmailDecision("reject", "sender domain blocked", email)
        return EmailDecision("forward", f"forward to {self.forward_to}", email)

    async def route(self, message: Any) -> IncomingEmail:
        email = self.inspect(message)
        decision = self.decide(email)
        if decision.action == "reject":
            message.setReject(decision.reason)
            return email
        headers = js.Headers.new()
        headers.set("X-Processed-By", "xampler-email-workers-19")
        await message.forward(self.forward_to, headers)
        return email


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        sample = IncomingEmail(
            sender="ada@example.com",
            recipient="search@example.net",
            subject="search: jeroen",
            size=128,
        )
        decision = EmailRouter(
            forward_to="archive@example.net", blocked_domains={"blocked.test"}
        ).decide(sample)
        return Response.json({
            "action": decision.action,
            "reason": decision.reason,
            "email": decision.email.__dict__,
        })

    async def email(self, message: Any, env: Any, ctx: Any) -> None:
        await EmailRouter(forward_to=str(env.FORWARD_TO)).route(message)
