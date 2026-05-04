from __future__ import annotations

import pytest

from xampler.experimental.email import EmailRouter, IncomingEmail
from xampler.experimental.htmlrewriter import OpenGraphPage, OpenGraphRewriter
from xampler.hyperdrive import DemoPostgres, HyperdriveConfig, PostgresQuery


def test_email_policy_fixture_decisions() -> None:
    router = EmailRouter(forward_to="archive@example.net", blocked_domains={"blocked.test"})
    allowed = router.decide(IncomingEmail("ada@example.com", "in@example.net", "hi", 10))
    blocked = router.decide(IncomingEmail("bot@blocked.test", "in@example.net", None, 10))
    assert allowed.action == "forward"
    assert blocked.action == "reject"


def test_htmlrewriter_fixture_transform() -> None:
    page = OpenGraphPage("Python & Workers", "Edge <HTML>", image_url="https://example/img.png")
    html = OpenGraphRewriter(page).transform("<html><head></head><body>Hello</body></html>")
    assert 'property="og:title"' in html
    assert "Python &amp; Workers" in html
    assert "Edge &lt;HTML&gt;" in html
    assert "og:image" in html


@pytest.mark.asyncio
async def test_hyperdrive_fixture_read_only_guard() -> None:
    config = HyperdriveConfig.from_binding(
        type(
            "Binding",
            (),
            {"connectionString": "postgres://db", "host": "db", "port": 5432},
        )()
    )
    assert config.host == "db"
    result = await DemoPostgres().query(PostgresQuery("SELECT * FROM notes"))
    assert result.row_count == 2
    with pytest.raises(ValueError):
        PostgresQuery("DELETE FROM notes").validate_read_only()
