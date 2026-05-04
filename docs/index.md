# Xampler Docs

Long-term docs are grouped by purpose. Older planning snapshots live in [`archive/`](archive/).

## Start here

1. [`api/vocabulary.md`](api/vocabulary.md) — the canonical Service/Ref/Request/Result/Event/Status vocabulary across Cloudflare products.
2. [`api/library-surface.md`](api/library-surface.md) — importable library modules, base classes, and stability levels.
3. [`api/reference.md`](api/reference.md) — concise API reference and copyable imports.
4. [`api/testability.md`](api/testability.md) — fake bindings, `Demo*` clients, and remote verification boundaries.

## API design details

- [`api/composition-and-operations.md`](api/composition-and-operations.md) — composition, checkpoint, retry, DLQ, workflow status, observability, and copyable pipeline patterns.
- [`api/unified-api-surface.md`](api/unified-api-surface.md) — the shared Xampler API shape.
- [`api/protocols.md`](api/protocols.md) — why real/demo services share capability Protocols instead of inheritance.
- [`api/primitives-api-surface.md`](api/primitives-api-surface.md) — primitive coverage and Pythonic API matrix.
- [`api/primitive-test-realism.md`](api/primitive-test-realism.md) — verification honesty matrix.
- [`api/native-python-workers-comparison.md`](api/native-python-workers-comparison.md) — Xampler wrappers vs native Python Workers bindings.
- [`api/pythonic-rubric.md`](api/pythonic-rubric.md) — scoring rubric.

## Runtime and platform grounding

- [`runtime/python-workers-runtime-guidance.md`](runtime/python-workers-runtime-guidance.md)
- [`runtime/pythonic-tooling.md`](runtime/pythonic-tooling.md)
- [`runtime/cloudflare-doc-links.md`](runtime/cloudflare-doc-links.md)
- [`runtime/credentials.md`](runtime/credentials.md)
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
- [`project/complex-example-backlog.md`](project/complex-example-backlog.md) — future app ideas and low-cost abstraction research.

## Maintainer notes and audits

These docs explain why the repo looks the way it does, but they are not the main user journey.

- [`project/competitive-positioning.md`](project/competitive-positioning.md)
- [`project/example-and-api-ideas.md`](project/example-and-api-ideas.md)
- [`project/complex-example-backlog.md`](project/complex-example-backlog.md)
- [`project/duplication-audit.md`](project/duplication-audit.md)
- [`project/experience-assessment.md`](project/experience-assessment.md)
- [`project/unfinished-work.md`](project/unfinished-work.md)
- [`project/lessons-learned.md`](project/lessons-learned.md)
