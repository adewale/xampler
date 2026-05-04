from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class ScheduledEventInfo:
    cron: str
    scheduled_time: datetime | None = None

    @classmethod
    def from_event(cls, event: Any) -> ScheduledEventInfo:
        timestamp = getattr(event, "scheduledTime", None)
        scheduled_time = None
        if timestamp is not None:
            scheduled_time = datetime.fromtimestamp(int(timestamp) / 1000, UTC)
        return cls(cron=str(event.cron), scheduled_time=scheduled_time)


@dataclass(frozen=True)
class ScheduledRunResult:
    cron: str
    message: str
    ok: bool = True


class ScheduledJob(Protocol):
    async def run(self, event: ScheduledEventInfo) -> ScheduledRunResult: ...


class DemoScheduledJob:
    async def run(self, event: ScheduledEventInfo) -> ScheduledRunResult:
        return ScheduledRunResult(
            cron=event.cron,
            message=f"ran scheduled job for {event.cron}",
        )
