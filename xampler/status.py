from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeVar

OperationState = Literal["not_started", "running", "complete", "failed"]


@dataclass(frozen=True)
class Progress:
    """Known-size work status."""
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
    """Resumable work position for imports, streams, and pipelines."""
    name: str
    offset: int
    records: int
    state: OperationState = "running"


T = TypeVar("T")


@dataclass(frozen=True)
class BatchResult[T]:
    """Grouped work result, usually paired with a checkpoint."""

    batches: int
    records: int
    checkpoint: T


__all__ = ["BatchResult", "Checkpoint", "OperationState", "Progress"]
