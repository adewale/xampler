from typing import Any, Self

class Response:
    def __init__(self, body: object = ..., init: object = ...) -> None: ...
    @classmethod
    def json(cls, data: object, init: object = ...) -> Self: ...

class WorkerEntrypoint:
    env: Any

class WorkflowEntrypoint:
    env: Any

class DurableObject:
    ctx: Any
    env: Any
    def __init__(self, ctx: Any, env: Any) -> None: ...
