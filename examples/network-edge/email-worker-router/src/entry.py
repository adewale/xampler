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
    if decision.action == "annotate":
        headers.set("X-Xampler-Annotation", decision.reason)
    await message.forward(router.forward_to, headers)
    return email


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        url = str(request.url)
        path = url.split("/fixtures/email/", 1)[-1] if "/fixtures/email/" in url else "forward"
        fixtures = {
            "allow": IncomingEmail("ada@trusted.test", "wiki@example.net", "hello", 128),
            "reject": IncomingEmail("bot@blocked.test", "wiki@example.net", "spam", 128),
            "forward": IncomingEmail("ada@example.com", "wiki@example.net", "search: jeroen", 128),
            "annotate": IncomingEmail(
                "ada@example.com", "wiki@example.net", "tag: needs-review", 128
            ),
        }
        sample = fixtures.get(path, fixtures["forward"])
        decision = EmailRouter(
            forward_to="archive@example.net",
            blocked_domains={"blocked.test"},
            allow_domains={"trusted.test"},
        ).decide(sample)
        return Response.json({
            "fixture": path,
            "action": decision.action,
            "reason": decision.reason,
            "email": decision.email.__dict__,
        })

    async def email(self, message: Any, env: Any, ctx: Any) -> None:
        await route_email(EmailRouter(forward_to=str(env.FORWARD_TO)), message)
