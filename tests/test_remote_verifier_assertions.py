from __future__ import annotations

import pytest

from scripts.verify_remote_examples import (
    RemoteCheck,
    assert_ai_gateway_response,
    assert_browser_scrape,
    assert_catalog_lifecycle,
    assert_catalog_tables,
    assert_r2_sql_select,
    assert_r2_sql_show_tables,
    assert_remote_response,
)


def test_remote_response_asserts_headers_size_and_json() -> None:
    check = RemoteCheck(
        "/image",
        content_type_contains="image/png",
        min_bytes=4,
        json_assert=None,
    )
    assert_remote_response(
        check,
        status=200,
        body="\x89PNG",
        body_bytes=b"\x89PNG",
        headers={"content-type": "image/png"},
    )

    with pytest.raises(AssertionError):
        assert_remote_response(
            check,
            status=200,
            body="x",
            body_bytes=b"x",
            headers={"content-type": "text/plain"},
        )


def test_remote_profile_json_assertions() -> None:
    assert_ai_gateway_response({"choices": [{"message": {"content": "hello"}}]})
    assert_browser_scrape({"title": "Example Domain"})
    assert_r2_sql_show_tables({"sql": "SHOW TABLES IN xampler", "data": ["gutenberg_smoke"]})
    assert_r2_sql_select({
        "sql": "SELECT * FROM xampler.gutenberg_smoke LIMIT 1",
        "data": {"table": "gutenberg_smoke"},
    })
    assert_catalog_tables({"tables": [{"name": "gutenberg_smoke"}]})
    assert_catalog_lifecycle({
        "namespace": "xampler_verify",
        "table": "temp_table",
        "lifecycle_complete": True,
        "tables_after_create": {"tables": [{"name": "temp_table"}]},
    })


@pytest.mark.parametrize(
    ("assertion", "payload"),
    [
        (assert_ai_gateway_response, {"choices": []}),
        (assert_browser_scrape, {"title": "Other"}),
        (assert_r2_sql_show_tables, {"sql": "SHOW TABLES IN xampler", "data": []}),
        (assert_catalog_tables, {"tables": []}),
        (assert_catalog_lifecycle, {"lifecycle_complete": False}),
    ],
)
def test_remote_profile_json_assertions_reject_weak_payloads(assertion, payload) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(AssertionError):
        assertion(payload)
