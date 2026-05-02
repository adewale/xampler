from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeVar

OperationState = Literal["not_started", "running", "complete", "failed"]


@dataclass(frozen=True)
class Progress:
    current: int
    total: int
    state: OperationState = "running"

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100.0)


@dataclass(frozen=True)
class Checkpoint:
    name: str
    offset: int
    records: int
    state: OperationState = "running"


T = TypeVar("T")


@dataclass(frozen=True)
class BatchResult[T]:
    batches: int
    records: int
    checkpoint: T
