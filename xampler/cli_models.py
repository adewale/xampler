from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

EXIT_OK = 0
EXIT_VERIFIER_FAILURE = 1
EXIT_USAGE = 2
EXIT_MISSING_CREDENTIALS = 3
EXIT_PROVIDER_FAILURE = 4
EXIT_REMOTE_SKIPPED = 5

REMOTE_ENV = "XAMPLER_RUN_REMOTE"
PREPARE_ENV = "XAMPLER_PREPARE_REMOTE"
CLEANUP_ENV = "XAMPLER_CLEANUP_REMOTE"


@dataclass(frozen=True)
class RemoteAdvice:
    credentials: tuple[str, ...]
    prepare: bool
    cost: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Surface:
    name: str
    example: str | None = None
    docs: str | None = None
    remote: RemoteAdvice | None = None


def _empty_env() -> Mapping[str, str]:
    return {}


@dataclass(frozen=True)
class CommandPlan:
    action: str
    surface: str
    command: tuple[str, ...]
    env: Mapping[str, str] = field(default_factory=_empty_env)
    cwd: str | None = None
    mutates: bool = False
    cost_warning: str | None = None
    description: str | None = None

    def payload(self, *, dry_run: bool) -> dict[str, object]:
        payload: dict[str, object] = {
            "action": self.action,
            "surface": self.surface,
            "command": list(self.command),
            "env": dict(self.env),
            "mutates": self.mutates,
            "dry_run": dry_run,
        }
        if self.cwd is not None:
            payload["cwd"] = self.cwd
        if self.cost_warning is not None:
            payload["cost_warning"] = self.cost_warning
        if self.description is not None:
            payload["description"] = self.description
        return payload


@dataclass(frozen=True)
class CliOptions:
    json_output: bool = False
    dry_run: bool = False
    quiet: bool = False
    verbose: int = 0
