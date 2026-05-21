from __future__ import annotations

from typing import cast

import pytest

from tests.test_r2_pythonic import FakeR2BucketBinding
from xampler.agent_tools import ToolApproval, create_r2_object_tools
from xampler.r2 import R2Bucket


@pytest.mark.asyncio
async def test_r2_agent_tools_are_approval_gated_and_read_only() -> None:
    bucket = R2Bucket(FakeR2BucketBinding())
    await bucket.put_text("notes/a.txt", "hello")

    tools = create_r2_object_tools(bucket)
    names = {tool.name for tool in tools}
    assert {"r2_list", "r2_read_text", "r2_write_text", "r2_delete"} <= names
    assert {tool.name for tool in tools if tool.requires_approval} == {"r2_write_text", "r2_delete"}

    by_name = {tool.name: tool for tool in tools}
    assert await by_name["r2_read_text"].call({"key": "notes/a.txt"}) == "hello"

    with pytest.raises(ToolApproval):
        await by_name["r2_delete"].call({"key": "notes/a.txt"})

    deleted = await by_name["r2_delete"].call({"key": "notes/a.txt"}, approved=True)
    assert deleted == {"deleted": True}
    assert await bucket.exists("notes/a.txt") is False

    read_only = create_r2_object_tools(bucket, read_only=True)
    assert {tool.name for tool in read_only} == {"r2_list", "r2_read_text", "r2_stat"}


@pytest.mark.asyncio
async def test_r2_agent_tool_validation_errors_are_model_visible() -> None:
    bucket = R2Bucket(FakeR2BucketBinding())
    tool = {tool.name: tool for tool in create_r2_object_tools(bucket)}["r2_read_text"]

    result = cast(dict[str, object], await tool.call({}))
    error = cast(dict[str, object], result["error"])
    assert error["code"] == "bad_request"
    assert "key" in str(error["message"])
