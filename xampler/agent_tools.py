from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from xampler.errors import XamplerError
from xampler.r2 import R2Bucket
from xampler.response import error_payload, jsonable

ToolHandler = Callable[[dict[str, object]], Awaitable[object]]


class ToolApproval(PermissionError):
    """Raised when a mutating tool is called without approval."""


@dataclass(frozen=True)
class AgentTool:
    """Small SDK-neutral tool definition for examples and agent adapters.

    The shape deliberately avoids depending on one agent SDK. Framework-specific
    adapters can translate this into OpenAI/Claude/MCP/Vercel tool definitions
    while preserving the same read/write and approval semantics.
    """

    name: str
    description: str
    input_schema: dict[str, object]
    handler: ToolHandler
    requires_approval: bool = False

    async def call(self, arguments: dict[str, object], *, approved: bool = False) -> object:
        if self.requires_approval and not approved:
            raise ToolApproval(f"{self.name} requires approval")
        try:
            return jsonable(await self.handler(arguments))
        except XamplerError as exc:
            return error_payload(exc)
        except (TypeError, ValueError, KeyError) as exc:
            return error_payload(str(exc), code="bad_request")


def _required_str(arguments: dict[str, object], name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _key_schema(*, include_value: bool = False) -> dict[str, object]:
    properties: dict[str, object] = {
        "key": {"type": "string", "description": "R2 object key"},
    }
    required = ["key"]
    if include_value:
        properties["value"] = {"type": "string", "description": "Text content to write"}
        required.append("value")
    return {"type": "object", "properties": properties, "required": required}


def create_r2_object_tools(
    bucket: R2Bucket,
    *,
    require_approval: bool | dict[str, bool] = True,
    read_only: bool = False,
) -> list[AgentTool]:
    """Expose an R2 bucket as SDK-neutral, approval-aware agent tools.

    Read tools never require approval. Mutating tools require approval by
    default. ``read_only=True`` removes mutating tools entirely, which is the
    safest shape for retrieval/summarization agents.
    """

    def approval(name: str) -> bool:
        if isinstance(require_approval, bool):
            return require_approval
        return require_approval.get(name, True)

    async def list_objects(arguments: dict[str, object]) -> object:
        prefix_value = arguments.get("prefix")
        prefix = prefix_value if isinstance(prefix_value, str) else None
        page = await bucket.list(prefix=prefix)
        return {"items": page.objects, "cursor": page.cursor, "truncated": page.truncated}

    async def read_text(arguments: dict[str, object]) -> object:
        key = _required_str(arguments, "key")
        text = await bucket.get_text(key)
        if text is None:
            raise XamplerError("not_found", f"R2 object not found: {key}")
        return text

    async def stat(arguments: dict[str, object]) -> object:
        key = _required_str(arguments, "key")
        info = await bucket.head(key)
        if info is None:
            raise XamplerError("not_found", f"R2 object not found: {key}")
        return info

    async def write_text(arguments: dict[str, object]) -> object:
        key = _required_str(arguments, "key")
        value = _required_str(arguments, "value")
        info = await bucket.put_text(key, value)
        return {"written": True, "info": info}

    async def delete(arguments: dict[str, object]) -> object:
        key = _required_str(arguments, "key")
        await bucket.delete(key)
        return {"deleted": True}

    tools = [
        AgentTool(
            "r2_list",
            "List R2 objects by optional prefix.",
            {
                "type": "object",
                "properties": {"prefix": {"type": "string"}},
                "required": [],
            },
            list_objects,
        ),
        AgentTool("r2_read_text", "Read a text object from R2.", _key_schema(), read_text),
        AgentTool(
            "r2_stat",
            "Fetch R2 object metadata without reading the body.",
            _key_schema(),
            stat,
        ),
    ]
    if read_only:
        return tools
    return [
        *tools,
        AgentTool(
            "r2_write_text",
            "Write text to an R2 object.",
            _key_schema(include_value=True),
            write_text,
            requires_approval=approval("r2_write_text"),
        ),
        AgentTool(
            "r2_delete",
            "Delete an R2 object.",
            _key_schema(),
            delete,
            requires_approval=approval("r2_delete"),
        ),
    ]


__all__ = ["AgentTool", "ToolApproval", "create_r2_object_tools"]
