# Xampler Docs

Long-term docs are grouped by purpose. Older planning snapshots live in [`archive/`](archive/).

## API design

- [`api/library-surface.md`](api/library-surface.md) — importable library modules and stability levels.
- [`api/reference.md`](api/reference.md) — concise API reference and copyable imports.
- [`api/unified-api-surface.md`](api/unified-api-surface.md) — the shared Xampler API shape.
- [`api/primitives-api-surface.md`](api/primitives-api-surface.md) — primitive coverage and Pythonic API matrix.
- [`api/primitive-test-realism.md`](api/primitive-test-realism.md) — verification honesty matrix.
- [`api/native-python-workers-comparison.md`](api/native-python-workers-comparison.md) — Xampler wrappers vs native Python Workers bindings.
- [`api/python-design-patterns.md`](api/python-design-patterns.md) — reusable wrapper patterns.
- [`api/pythonic-rubric.md`](api/pythonic-rubric.md) — scoring rubric.
- [`api/cloudflare-python-api-shape.md`](api/cloudflare-python-api-shape.md) — general API target.

## Runtime and platform grounding

- [`runtime/python-workers-runtime-guidance.md`](runtime/python-workers-runtime-guidance.md)
- [`runtime/pythonic-tooling.md`](runtime/pythonic-tooling.md)
- [`runtime/cloudflare-doc-links.md`](runtime/cloudflare-doc-links.md)
- [`runtime/remote-verification.md`](runtime/remote-verification.md)
- [`runtime/local-path-development.md`](runtime/local-path-development.md)
- [`runtime/cloudflare-best-practices-alignment.md`](runtime/cloudflare-best-practices-alignment.md)

## Data and streaming

- [`data/datasets.md`](data/datasets.md)
- [`data/streaming-api.md`](data/streaming-api.md)
- [`data/s3-python-library-research.md`](data/s3-python-library-research.md)

## Project direction

These are mostly maintainer-facing. New users should start with the API/runtime/data docs above.

- [`project/example-categories.md`](project/example-categories.md) — user-facing categorization by realism and product family.
- [`project/project-structure-and-naming.md`](project/project-structure-and-naming.md) — folder and naming conventions.
- [`project/composite-example-backlog.md`](project/composite-example-backlog.md) — future app ideas.

## Maintainer notes and audits

These docs explain why the repo looks the way it does, but they are not the main user journey.

- [`project/lessons-learned.md`](project/lessons-learned.md)
- [`project/gaps-explained.md`](project/gaps-explained.md)
- [`project/original-goals-audit.md`](project/original-goals-audit.md)
- [`project/shared-wrapper-candidates.md`](project/shared-wrapper-candidates.md)
- [`project/wrapper-consistency-audit.md`](project/wrapper-consistency-audit.md)
