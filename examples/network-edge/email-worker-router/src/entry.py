from __future__ import annotations

from typing import Any

import js  # type: ignore[import-not-found]
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.experimental.email import EmailRouter, IncomingEmail


async def route_email(router: EmailRouter, message: Any) -> IncomingEmail:
    email = IncomingEmail.from_message(message)
    decision = router.decide(email)
    if decision.action == "reject":
        message.setReject(decision.reason)
        return email
    headers = js.Headers.new()
    headers.set("X-Processed-By", "xampler-email-workers-19")
    await message.forward(router.forward_to, headers)
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
        await route_email(EmailRouter(forward_to=str(env.FORWARD_TO)), message)
