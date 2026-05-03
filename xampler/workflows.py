from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from .cloudflare import CloudflareService, ResourceRef
from .status import OperationState


@dataclass(frozen=True)
class WorkflowStart:
    instance_id: str


@dataclass(frozen=True)
class WorkflowStatus:
    instance_id: str
    status: OperationState
    raw: object | None = None


def parse_workflow_state(value: object) -> OperationState:
    state = str(value)
    if state in {"not_started", "running", "complete", "failed"}:
        return cast(OperationState, state)
    return "running"


class WorkflowInstance(ResourceRef[Any]):
    def __init__(self, instance_id: str, raw: Any):
        super().__init__(name=instance_id, raw=raw)
        object.__setattr__(self, "id", instance_id)

    async def status(self) -> WorkflowStatus:
        raw_status = cast(object, await self.raw.status())
        raw_state: object = raw_status
        if isinstance(raw_status, dict):
            raw_status_map = cast(dict[object, object], raw_status)
            raw_state = raw_status_map.get("status", "running")
        return WorkflowStatus(
            instance_id=self.name,
            status=parse_workflow_state(raw_state),
            raw=cast(object, raw_status),
        )


class WorkflowService(CloudflareService[Any]):
    async def start(self) -> WorkflowStart:
        instance = await self.raw.create()
        return WorkflowStart(instance_id=str(instance.id))

    async def instance(self, instance_id: str) -> WorkflowInstance:
        return WorkflowInstance(instance_id, await self.raw.get(instance_id))

    async def status(self, instance_id: str) -> WorkflowStatus:
        return await (await self.instance(instance_id)).status()


class DemoWorkflowService:
    def __init__(
        self, *, instance_id: str = "demo-instance", status: OperationState | None = None
    ) -> None:
        self.started = WorkflowStart(instance_id)
        self.demo_status: OperationState = "complete" if status is None else status

    async def start(self) -> WorkflowStart:
        return self.started

    async def status(self, instance_id: str) -> WorkflowStatus:
        return WorkflowStatus(instance_id=instance_id, status=self.demo_status, raw={"demo": True})
