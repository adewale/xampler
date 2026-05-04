from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

EmailAction = Literal["allow", "forward", "reject", "annotate"]


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
    def __init__(
        self,
        *,
        forward_to: str,
        blocked_domains: set[str] | None = None,
        allow_domains: set[str] | None = None,
        annotate_subject_prefixes: tuple[str, ...] = ("tag:",),
    ):
        self.forward_to = forward_to
        self.blocked_domains = blocked_domains or set()
        self.allow_domains = allow_domains or set()
        self.annotate_subject_prefixes = annotate_subject_prefixes

    def decide(self, email: IncomingEmail) -> EmailDecision:
        domain = email.sender.rsplit("@", 1)[-1]
        if domain in self.blocked_domains:
            return EmailDecision("reject", "sender domain blocked", email)
        if domain in self.allow_domains:
            return EmailDecision("allow", "sender domain explicitly allowed", email)
        subject = email.subject or ""
        if subject.startswith(self.annotate_subject_prefixes):
            return EmailDecision("annotate", "annotate message before forwarding", email)
        return EmailDecision("forward", f"forward to {self.forward_to}", email)
