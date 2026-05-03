from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["user", "assistant", "tool", "system"]


@dataclass(frozen=True)
class AgentMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, object] = field(default_factory=lambda: {})


@dataclass(frozen=True)
class AgentRunResult:
    messages: list[AgentMessage]
    tool_calls: list[ToolCall] = field(default_factory=lambda: [])
    raw: object | None = None


class DemoAgent:
    def __init__(self, *, name: str = "demo-agent"):
        self.name = name

    async def run(self, message: str) -> AgentRunResult:
        return AgentRunResult(
            messages=[
                AgentMessage("user", message),
                AgentMessage("assistant", f"{self.name} handled: {message}"),
            ],
            raw={"demo": True},
        )


class AgentSession:
    def __init__(self, raw: Any):
        self.raw = raw

    async def run(self, message: str) -> AgentRunResult:
        result = await self.raw.run(message)
        if isinstance(result, AgentRunResult):
            return result
        return AgentRunResult(messages=[AgentMessage("assistant", str(result))], raw=result)
