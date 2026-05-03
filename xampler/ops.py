from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .status import Checkpoint, OperationState, Progress


def _empty_events() -> list[TimelineEvent]:
    return []


@dataclass(frozen=True)
class TimelineEvent:
    name: str
    state: OperationState = "running"
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class OperationTimeline:
    id: str
    events: list[TimelineEvent] = field(default_factory=_empty_events)

    @property
    def state(self) -> OperationState:
        if not self.events:
            return "not_started"
        if any(event.state == "failed" for event in self.events):
            return "failed"
        if all(event.state == "complete" for event in self.events):
            return "complete"
        return "running"


@dataclass(frozen=True)
class PipelineStatus:
    name: str
    progress: Progress
    checkpoint: Checkpoint | None = None
    timeline: OperationTimeline | None = None
