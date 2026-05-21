from __future__ import annotations

import pytest

from xampler.ai_gateway import _js_module as ai_gateway_js
from xampler.browser_rendering import _js_module as browser_js
from xampler.errors import XamplerError, ensure_supported_runtime, provider_error, unsupported
from xampler.hyperdrive import HyperdriveConfig, HyperdrivePostgres, PostgresQuery
from xampler.r2_data_catalog import _js_module as catalog_js
from xampler.r2_sql import R2SqlQuery


def test_error_helpers_preserve_codes_and_causes() -> None:
    cause = RuntimeError("raw provider failed")
    error = provider_error("provider call failed", cause=cause)
    assert error.code == "provider"
    assert error.cause is cause

    with pytest.raises(XamplerError) as exc_info:
        ensure_supported_runtime(False, "missing runtime")
    assert exc_info.value.code == "unsupported"

    error = unsupported("no signer configured")
    assert error.code == "unsupported"


@pytest.mark.parametrize("loader", [ai_gateway_js, browser_js, catalog_js])
def test_runtime_loaders_raise_xampler_error_outside_workers(loader) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(XamplerError) as exc_info:
        loader()
    assert exc_info.value.code == "unsupported"
    assert "Workers runtime" in str(exc_info.value)


def test_r2_sql_guard_uses_normalized_error_codes() -> None:
    with pytest.raises(XamplerError) as bad_request:
        R2SqlQuery("DELETE FROM x").safe_sql()
    assert bad_request.value.code == "bad_request"

    with pytest.raises(XamplerError) as unsupported_info:
        R2SqlQuery("SELECT * FROM a JOIN b ON a.id = b.id").safe_sql()
    assert unsupported_info.value.code == "unsupported"


def test_hyperdrive_unconfigured_client_uses_unsupported_error() -> None:
    with pytest.raises(XamplerError) as exc_info:
        # Query validation passes; the deployed-client path is the unsupported part.
        import asyncio

        client = HyperdrivePostgres(HyperdriveConfig(connection_string="postgres://demo"))
        asyncio.run(client.query(PostgresQuery("SELECT 1")))
    assert exc_info.value.code == "unsupported"
