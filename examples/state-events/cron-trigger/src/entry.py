from __future__ import annotations

from typing import Any

from workers import Response, WorkerEntrypoint

from xampler.experimental.cron import DemoScheduledJob, ScheduledEventInfo


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        return Response("scheduled worker is alive")

    async def scheduled(self, event: Any, env: Any, ctx: Any) -> None:
        result = await DemoScheduledJob().run(ScheduledEventInfo.from_event(event))
        print(result.message)
