from __future__ import annotations

import os

from xampler.cli_models import RemoteAdvice, Surface

SURFACES: dict[str, Surface] = {
    "agents": Surface(
        "agents", "examples/ai-agents/agents-sdk-tools", "docs/api/reference/agents.md"
    ),
    "ai": Surface("ai", "examples/ai-agents/workers-ai-inference", "docs/api/reference/ai.md"),
    "ai-gateway": Surface(
        "ai-gateway",
        "examples/ai-agents/ai-gateway-chat",
        "docs/api/reference/ai-gateway.md",
        RemoteAdvice(
            (
                "CLOUDFLARE_ACCOUNT_ID",
                "CLOUDFLARE_API_TOKEN",
                "XAMPLER_AI_GATEWAY_ID",
                "OPENAI_API_KEY",
            ),
            False,
            "May incur provider costs; default model is openai/gpt-4o-mini unless "
            "XAMPLER_AI_GATEWAY_MODEL is set.",
        ),
    ),
    "browser-rendering": Surface(
        "browser-rendering",
        "examples/network-edge/browser-rendering-screenshot",
        "docs/api/reference/browser-rendering.md",
        RemoteAdvice(
            ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
            True,
            "May incur Browser Rendering usage charges.",
            ("Run `xc remote prepare browser-rendering` before verify.",),
        ),
    ),
    "cron": Surface("cron", "examples/state-events/cron-trigger", "docs/api/reference/cron.md"),
    "d1": Surface("d1", "examples/storage-data/d1-database", "docs/api/reference/d1.md"),
    "durable-objects": Surface(
        "durable-objects",
        "examples/state-events/durable-object-chatroom",
        "docs/api/reference/durable-objects.md",
    ),
    "dynamic-workers": Surface(
        "dynamic-workers",
        "examples/experimental/dynamic-workers-loader",
        "docs/api/reference/dynamic-workers.md",
    ),
    "email": Surface(
        "email", "examples/network-edge/email-worker-router", "docs/api/reference/email.md"
    ),
    "gutenberg": Surface("gutenberg", "examples/streaming/gutenberg-stream-composition"),
    "htmlrewriter": Surface(
        "htmlrewriter",
        "examples/network-edge/htmlrewriter-opengraph",
        "docs/api/reference/htmlrewriter.md",
    ),
    "hyperdrive": Surface(
        "hyperdrive",
        "examples/storage-data/hyperdrive-postgres",
        "docs/api/reference/hyperdrive.md",
    ),
    "kv": Surface("kv", "examples/storage-data/kv-namespace", "docs/api/reference/kv.md"),
    "mini-wiki": Surface("mini-wiki", "examples/full-apps/mini-wiki"),
    "python-by-example": Surface(
        "python-by-example", "examples/experimental/python-by-example-playground"
    ),
    "queues": Surface(
        "queues", "examples/state-events/queues-producer-consumer", "docs/api/reference/queues.md"
    ),
    "r2": Surface("r2", "examples/storage-data/r2-object-storage", "docs/api/reference/r2.md"),
    "r2-data-catalog": Surface(
        "r2-data-catalog",
        "examples/storage-data/r2-data-catalog",
        "docs/api/reference/r2-data-catalog.md",
        RemoteAdvice(
            (
                "CLOUDFLARE_ACCOUNT_ID",
                "XAMPLER_R2_DATA_CATALOG_TOKEN or WRANGLER_R2_SQL_AUTH_TOKEN",
            ),
            True,
            "May create/use R2 Data Catalog namespaces/tables.",
        ),
    ),
    "r2-sql": Surface(
        "r2-sql",
        "examples/storage-data/r2-sql",
        "docs/api/reference/r2-sql.md",
        RemoteAdvice(
            ("CLOUDFLARE_ACCOUNT_ID", "WRANGLER_R2_SQL_AUTH_TOKEN"),
            True,
            "May create/use an R2 bucket, catalog, and R2 SQL queries.",
        ),
    ),
    "service-bindings": Surface(
        "service-bindings",
        "examples/network-edge/service-bindings-rpc/ts",
        "docs/api/reference/service-bindings.md",
    ),
    "status": Surface("status", docs="docs/api/reference/status.md"),
    "vectorize": Surface(
        "vectorize",
        "examples/ai-agents/vectorize-search",
        "docs/api/reference/vectorize.md",
        RemoteAdvice(("CLOUDFLARE_ACCOUNT_ID",), True, "May create/use a Vectorize index."),
    ),
    "vocabulary": Surface("vocabulary", docs="docs/api/vocabulary.md"),
    "websockets": Surface(
        "websockets",
        "examples/network-edge/outbound-websocket-consumer",
        "docs/api/reference/websockets.md",
    ),
    "workers-ai": Surface(
        "workers-ai",
        "examples/ai-agents/workers-ai-inference",
        None,
        RemoteAdvice(("CLOUDFLARE_ACCOUNT_ID",), True, "May incur Workers AI usage charges."),
    ),
    "workflows": Surface(
        "workflows", "examples/state-events/workflows-pipeline", "docs/api/reference/workflows.md"
    ),
}


def examples() -> dict[str, str]:
    return {
        name: surface.example
        for name, surface in SURFACES.items()
        if surface.example is not None
    }


def docs() -> dict[str, str]:
    return {name: surface.docs for name, surface in SURFACES.items() if surface.docs is not None}


def surface_choices(*, require_example: bool = False, require_docs: bool = False) -> list[str]:
    return sorted(
        name
        for name, surface in SURFACES.items()
        if (not require_example or surface.example is not None)
        and (not require_docs or surface.docs is not None)
    )


def credential_status(name: str) -> str:
    if " or " in name:
        any_set = any(os.environ.get(part.strip()) for part in name.split(" or "))
        return "set" if any_set else "missing"
    return "set" if os.environ.get(name) else "missing"
