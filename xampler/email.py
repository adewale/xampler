from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

EmailAction = Literal["forward", "reject"]


@dataclass(frozen=True)
class IncomingEmail:
    sender: str
    recipient: str
    subject: str | None
    size: int

    @classmethod
    def from_message(cls, message: Any) -> IncomingEmail:
        return cls(
            sender=str(message.from_),
            recipient=str(message.to),
            subject=message.headers.get("subject"),
            size=int(message.rawSize),
        )


@dataclass(frozen=True)
class EmailDecision:
    action: EmailAction
    reason: str
    email: IncomingEmail


class EmailRouter:
    def __init__(self, *, forward_to: str, blocked_domains: set[str] | None = None):
        self.forward_to = forward_to
        self.blocked_domains = blocked_domains or set()

    def decide(self, email: IncomingEmail) -> EmailDecision:
        domain = email.sender.rsplit("@", 1)[-1]
        if domain in self.blocked_domains:
            return EmailDecision("reject", "sender domain blocked", email)
        return EmailDecision("forward", f"forward to {self.forward_to}", email)
